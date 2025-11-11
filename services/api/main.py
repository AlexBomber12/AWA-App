import asyncio
import os
from collections.abc import Callable, Iterable
from contextlib import asynccontextmanager

import httpx
import redis.asyncio as aioredis
import structlog
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.db.async_session import (
    dispose_async_engine,
    get_async_engine,
    get_async_session,
    get_sessionmaker,
    init_async_engine,
)
from awa_common.logging import RequestIdMiddleware, configure_logging
from awa_common.loop_lag import start_loop_lag_monitor
from awa_common.metrics import MetricsMiddleware, init as metrics_init, register_metrics_endpoint
from awa_common.security.headers import install_security_headers
from awa_common.security.ratelimit import install_role_based_rate_limit
from awa_common.security.request_limits import install_body_size_limit
from awa_common.settings import settings
from services.api.errors import install_exception_handlers
from services.api.middlewares.audit import AuditMiddleware
from services.api.security import install_security
from services.api.sentry_config import init_sentry_if_configured

from .routes import health as health_router
from .routes.ingest import router as ingest_router
from .routes.roi import router as roi_router
from .routes.score import router as score_router
from .routes.sku import router as sku_router
from .routes.stats import router as stats_router
from .routes.upload import router as upload_router


async def ready_db(session: AsyncSession = Depends(get_async_session)) -> dict[str, str]:
    """Return 200 only when migrations are at head."""
    alembic_config = os.getenv("ALEMBIC_CONFIG", "services/api/alembic.ini")
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
    env = (app_env or getattr(settings, "APP_ENV", "dev")).strip().lower()
    raw_origins = configured_origins
    if raw_origins is None:
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
    redis_url = settings.REDIS_URL
    r = None
    lag_stop: Callable[[], None] | None = None
    try:
        if settings.ENABLE_LOOP_LAG_MONITOR:
            lag_stop = start_loop_lag_monitor(asyncio.get_running_loop(), float(settings.LOOP_LAG_INTERVAL_S))
            _app.state.loop_lag_stop = lag_stop
        r = await _wait_for_redis(redis_url)
        await FastAPILimiter.init(r)
    except Exception as exc:
        structlog.get_logger().warning("redis_unavailable", error=str(exc))
        r = None
    try:
        yield
    finally:
        if lag_stop is not None:
            lag_stop()
            _app.state.loop_lag_stop = None
        if r is not None:
            try:
                await FastAPILimiter.close()
            except RuntimeError:
                pass
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
    install_role_based_rate_limit(app, cfg)
    app.state.loop_lag_stop = None

    app.include_router(upload_router, prefix="/upload")
    app.include_router(ingest_router)
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
    env = os.getenv("ENV", getattr(settings, "ENV", "local")).lower()
    if max_attempts is None:
        max_attempts = int(
            os.getenv(
                "WAIT_FOR_DB_MAX_ATTEMPTS",
                "10" if env in {"local", "test"} else "50",
            )
        )
    if delay_s is None:
        delay_s = float(os.getenv("WAIT_FOR_DB_DELAY_S", "0.05" if env in {"local", "test"} else "0.2"))
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


async def _wait_for_redis(url: str) -> aioredis.Redis:
    delay = 0.2
    for _ in range(50):
        try:
            r = aioredis.from_url(url, encoding="utf-8", decode_responses=True)
            await r.ping()
            return r
        except Exception:
            await asyncio.sleep(delay)
    raise RuntimeError("Redis not available")


async def _check_llm() -> None:
    """Verify the configured LLM provider is reachable.

    Any import or network failure should not block application startup; instead
    we fall back to the stub provider so the service can continue running.
    """

    provider = os.getenv("LLM_PROVIDER", getattr(settings, "LLM_PROVIDER", "stub")).lower()
    lan_base = os.getenv("LAN_BASE", "http://lan-llm:8000")
    if provider != "lan":
        return
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            await client.get(f"{lan_base}/ready")
    except Exception:
        fallback = os.getenv("LLM_PROVIDER_FALLBACK", "stub").lower()
        os.environ["LLM_PROVIDER"] = fallback
        try:
            settings.LLM_PROVIDER = fallback  # type: ignore[attr-defined]
        except Exception:
            pass


__all__ = ["app", "create_app", "ready", "ready_db"]
