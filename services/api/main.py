import asyncio
import inspect
import os
from collections.abc import Callable, Iterable
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
import sentry_sdk
import structlog
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.cache import (
    cache as shared_cache,
    close_cache,
    configure_cache_backend,
    normalize_namespace,
    ping_cache,
)
from awa_common.db.async_session import (
    dispose_async_engine,
    get_async_engine,
    get_async_session,
    get_sessionmaker,
    init_async_engine,
)
from awa_common.http_client import AsyncHTTPClient
from awa_common.logging import RequestIdMiddleware, configure_logging
from awa_common.loop_lag import start_loop_lag_monitor
from awa_common.metrics import MetricsMiddleware, init as metrics_init, record_redis_error, register_metrics_endpoint
from awa_common.security import oidc as oidc_provider
from awa_common.security.headers import install_security_headers
from awa_common.security.request_limits import install_body_size_limit
from awa_common.settings import settings
from awa_common.utils.env import env_bool, env_str
from services.api.errors import install_exception_handlers
from services.api.middlewares.audit import AuditMiddleware
from services.api.security import install_security
from services.api.sentry_config import init_sentry_if_configured

from .routes import health as health_router
from .routes.decision_engine import router as decision_router
from .routes.inbox import router as inbox_router
from .routes.ingest import router as ingest_router
from .routes.roi import router as roi_router
from .routes.score import router as score_router
from .routes.sku import router as sku_router
from .routes.stats import router as stats_router
from .routes.upload import router as upload_router

_BASE_LLM_PROVIDER = getattr(settings, "LLM_PROVIDER", "stub").lower()


async def ready_db(session: AsyncSession = Depends(get_async_session)) -> dict[str, str]:
    """Return 200 only when migrations are at head."""
    alembic_config = getattr(getattr(settings, "app", None), "config_path", "services/api/alembic.ini")
    cfg = Config(alembic_config)
    head = ScriptDirectory.from_config(cfg).get_current_head()
    result = await session.execute(sa_text("SELECT version_num FROM alembic_version"))
    current = result.scalar()
    if current == head:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="migrations pending")


def ready() -> dict[str, str]:
    return {"status": "ok", "env": settings.ENV}


def _normalize_cors_origins(value: str | Iterable[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = value.split(",")
    else:
        items = list(value)
    origins = []
    for item in items:
        candidate = item.strip()
        if candidate:
            origins.append(candidate)
    return origins


def resolve_cors_origins(
    app_env: str | None = None, configured_origins: str | Iterable[str] | None = None
) -> list[str]:
    env = app_env or getattr(settings, "APP_ENV", "dev")
    env = (env or "dev").strip().lower()
    raw_origins = configured_origins
    if raw_origins is None:
        security_cfg = getattr(settings, "security", None)
        if security_cfg and security_cfg.cors_origins:
            raw_origins = security_cfg.cors_origins
        else:
            raw_origins = getattr(settings, "CORS_ORIGINS", None)

    origins = _normalize_cors_origins(raw_origins)

    if not origins:
        if env == "dev":
            return ["http://localhost:3000"]
        if env in {"stage", "staging", "prod", "production"}:
            raise RuntimeError("CORS_ORIGINS must be set when APP_ENV is 'stage' or 'prod'.")
        return []

    if env in {"stage", "staging", "prod", "production"} and any(origin == "*" for origin in origins):
        raise RuntimeError("Wildcard origins are not permitted in stage or prod environments.")

    return origins


def install_cors(app: FastAPI) -> None:
    origins = resolve_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=600,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_async_engine()
    await _wait_for_db()
    await _check_llm()
    redis_cfg = getattr(settings, "redis", None)
    redis_url = redis_cfg.url if redis_cfg else settings.REDIS_URL
    stats_enabled = env_bool("STATS_ENABLE_CACHE", default=getattr(settings, "STATS_ENABLE_CACHE", False))
    limiter_redis: aioredis.Redis | None = None
    _app.state.stats_cache = None
    _app.state.stats_cache_namespace = normalize_namespace(
        redis_cfg.cache_namespace if redis_cfg else getattr(settings, "STATS_CACHE_NAMESPACE", "stats:")
    )
    _app.state.redis_health = {
        "critical": bool(redis_cfg.health_critical if redis_cfg else getattr(settings, "REDIS_HEALTH_CRITICAL", False)),
        "status": "unknown",
        "error": None,
    }
    _app.state.redis_url = redis_url
    _app.state.limiter_redis = None
    lag_stop: Callable[[], None] | None = None
    jwks_started = False
    log = structlog.get_logger(__name__)
    try:
        if settings.ENABLE_LOOP_LAG_MONITOR:
            lag_stop = start_loop_lag_monitor(asyncio.get_running_loop(), float(settings.LOOP_LAG_INTERVAL_S))
            _app.state.loop_lag_stop = lag_stop
        try:
            limiter_redis = await _wait_for_redis(redis_url)
        except TypeError:
            limiter_redis = await _wait_for_redis()  # type: ignore[call-arg]
        await FastAPILimiter.init(limiter_redis)
        _app.state.limiter_redis = limiter_redis
        _update_redis_health(_app.state, status="ok")
    except Exception as exc:
        log.error("redis_unavailable", error=str(exc))
        record_redis_error("lifespan", "ping", key="rate_limit")
        sentry_sdk.capture_exception(exc)
        limiter_redis = None
        _app.state.limiter_redis = None
        _update_redis_health(_app.state, status="degraded", error=str(exc))
        if bool(redis_cfg.health_critical if redis_cfg else getattr(settings, "REDIS_HEALTH_CRITICAL", False)):
            raise
    try:
        if stats_enabled:
            cache_url = redis_cfg.cache_url if redis_cfg else getattr(settings, "CACHE_REDIS_URL", None) or redis_url
            await configure_cache_backend(cache_url, suppress=False)
            cache_ok = await ping_cache()
            if not cache_ok:
                raise RuntimeError("stats cache backend unavailable")
            _app.state.stats_cache = shared_cache
            _update_redis_health(_app.state, status="ok")
    except Exception as exc:
        log.error("stats_cache_unavailable", error=str(exc))
        record_redis_error("stats_cache", "ping", key="stats_cache")
        sentry_sdk.capture_exception(exc)
        _app.state.stats_cache = None
        await close_cache()
        _update_redis_health(_app.state, status="degraded", error=str(exc))
        if getattr(settings, "REDIS_HEALTH_CRITICAL", False):
            raise
    await oidc_provider.init_async_jwks_provider(settings)
    jwks_started = True
    try:
        yield
    finally:
        if lag_stop is not None:
            lag_stop()
            _app.state.loop_lag_stop = None
        if jwks_started:
            await oidc_provider.shutdown_async_jwks_provider()
        if stats_enabled:
            await close_cache()
            _app.state.stats_cache = None
        if limiter_redis is not None:
            try:
                await FastAPILimiter.close()
            except RuntimeError:
                pass
            await _close_redis_client(limiter_redis)
            _app.state.limiter_redis = None
        await dispose_async_engine()


def create_app() -> FastAPI:
    cfg = settings
    app_version = getattr(cfg, "APP_VERSION", "0.0.0")
    configure_logging(service="api", level=cfg.LOG_LEVEL)
    metrics_init(service="api", env=cfg.ENV, version=app_version)
    init_sentry_if_configured()
    structlog.get_logger(__name__).info("api.settings", settings=cfg.redacted())

    app = FastAPI(lifespan=lifespan)

    install_security_headers(app, cfg)
    install_body_size_limit(app, cfg)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(MetricsMiddleware)
    install_security(app)
    app.add_middleware(AuditMiddleware, session_factory=lambda: get_sessionmaker()())
    install_exception_handlers(app)
    register_metrics_endpoint(app)
    install_cors(app)
    app.state.loop_lag_stop = None

    app.include_router(upload_router, prefix="/upload")
    app.include_router(ingest_router)
    app.include_router(inbox_router)
    app.include_router(decision_router)
    app.include_router(roi_router)
    app.include_router(stats_router)
    app.include_router(score_router)
    app.include_router(sku_router)
    app.include_router(health_router.router)
    app.add_api_route(
        "/ready_db",
        ready_db,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
    )
    app.add_api_route("/ready", ready, methods=["GET"])

    return app


app = create_app()


async def _wait_for_db(max_attempts: int | None = None, delay_s: float | None = None) -> None:
    app_cfg = getattr(settings, "app", None)
    env = (app_cfg.env if app_cfg else getattr(settings, "ENV", "local")).lower()
    if max_attempts is None:
        max_attempts = settings.wait_for_db_max_attempts
    if delay_s is None:
        delay_s = settings.wait_for_db_delay_s
    engine = get_async_engine()
    last_err: Exception | None = None
    for _ in range(max_attempts):
        try:
            async with engine.connect() as conn:
                await conn.execute(sa_text("SELECT 1"))
            last_err = None
            break
        except Exception as exc:
            last_err = exc
            await asyncio.sleep(delay_s)
    if last_err and env not in {"local", "test"}:
        raise last_err


async def _wait_for_redis(url: str | None = None) -> aioredis.Redis:
    delay = 0.2
    app_env = str(getattr(settings, "APP_ENV", "dev") or "dev").lower()
    attempts = 5 if app_env in {"dev", "local", "test"} else 50
    redis_cfg = getattr(settings, "redis", None)
    redis_url = url or (redis_cfg.url if redis_cfg else getattr(settings, "REDIS_URL", "redis://localhost/0"))
    for _ in range(attempts):
        try:
            r = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await asyncio.wait_for(r.ping(), timeout=1.0)
            return r
        except Exception:
            await asyncio.sleep(delay)
    raise RuntimeError("Redis not available")


async def _check_llm() -> None:
    """Verify the configured LLM provider is reachable.

    Any import or network failure should not block application startup; instead
    we fall back to the stub provider so the service can continue running.
    """

    global _BASE_LLM_PROVIDER

    cfg = settings
    env_provider = env_str("LLM_PROVIDER")
    env_lower = env_provider.lower() if env_provider else None
    current_provider = getattr(cfg, "LLM_PROVIDER", None)
    current_lower = (current_provider or "stub").lower()
    use_env = env_lower is not None and (current_lower == _BASE_LLM_PROVIDER or current_provider is None)
    if use_env and env_lower is not None and env_lower != current_lower:
        object.__setattr__(cfg, "LLM_PROVIDER", env_provider)
        cfg.__dict__["LLM_PROVIDER"] = env_provider
        cfg.__dict__.pop("llm", None)
        try:
            cfg.model_fields_set.add("LLM_PROVIDER")
        except Exception:
            pass
        globals()["settings"] = cfg
        current_lower = env_lower
        _BASE_LLM_PROVIDER = env_lower

    llm_cfg = getattr(cfg, "llm", None)
    provider = (llm_cfg.provider if llm_cfg else current_lower or "local").lower()
    local_base = getattr(llm_cfg, "provider_base_url", None) or getattr(cfg, "LLM_PROVIDER_BASE_URL", None) or ""
    lan_timeout = float(getattr(llm_cfg, "lan_health_timeout_s", getattr(cfg, "LLM_LAN_HEALTH_TIMEOUT_S", 1.0)))
    if provider != "local":
        return
    try:
        async with AsyncHTTPClient(
            integration="llm_health",
            total_timeout_s=lan_timeout,
            max_retries=1,
        ) as client:
            if local_base:
                await client.get(f"{local_base}/ready", timeout=lan_timeout)
    except Exception:
        fallback_source = (
            (llm_cfg.secondary_provider if llm_cfg else None)
            or getattr(cfg, "LLM_SECONDARY_PROVIDER", None)
            or provider
            or "local"
        )
        fallback = fallback_source.lower()
        os.environ["LLM_PROVIDER"] = fallback
        object.__setattr__(cfg, "LLM_PROVIDER", fallback)
        cfg.__dict__["LLM_PROVIDER"] = fallback
        cfg.__dict__.pop("llm", None)
        try:
            cfg.model_fields_set.add("LLM_PROVIDER")
        except Exception:
            pass
        cfg.__dict__.pop("llm", None)
        globals()["settings"] = cfg
        _BASE_LLM_PROVIDER = fallback


async def _close_redis_client(client: aioredis.Redis | None) -> None:
    if client is None:
        return
    close = getattr(client, "aclose", None)
    if callable(close):
        await close()
        return
    close = getattr(client, "close", None)
    if callable(close):
        result = close()
        if inspect.isawaitable(result):
            await result


def _update_redis_health(state, *, status: str, error: str | None = None) -> None:
    try:
        health = getattr(state, "redis_health", None)
        if isinstance(health, dict):
            health["status"] = status
            health["error"] = error
    except Exception:
        pass


__all__ = ["app", "create_app", "ready", "ready_db"]
