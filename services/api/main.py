import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

import httpx
import redis.asyncio as aioredis
import sqlalchemy
import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from awa_common.settings import settings
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import Response

from alembic.config import Config
from alembic.script import ScriptDirectory
from services.api.errors import install_exception_handlers
from services.api.logging_config import configure_logging
from services.api.sentry_config import init_sentry_if_configured

from .db import get_session
from .routes import health as health_router
from .routes.ingest import router as ingest_router
from .routes.roi import router as roi_router
from .routes.score import router as score_router
from .routes.stats import router as stats_router
from .routes.upload import router as upload_router

configure_logging()
init_sentry_if_configured()
logging.getLogger(__name__).info("settings=%s", json.dumps(settings.redacted()))


def _is_truthy(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "y"}


async def client_ip_identifier(request: Request) -> str:
    if _is_truthy(os.getenv("TRUST_X_FORWARDED", "1")):
        xff = request.headers.get("x-forwarded-for")
        if xff:
            # first IP in the chain
            ip = xff.split(",")[0].strip()
            if ip:
                return ip
        xri = request.headers.get("x-real-ip")
        if xri:
            return xri.strip()
    client = request.client
    if not client or not getattr(client, "host", None):
        return "unknown"
    return client.host


def _parse_rate_limit(s: str) -> tuple[int, int]:
    # formats: "100/minute", "60/second", "1000/hour"
    try:
        n, unit = s.split("/", 1)
        times = int(n.strip())
        unit = unit.strip().lower()
    except Exception:
        return 100, 60
    if unit.startswith("min"):
        seconds = 60
    elif unit.startswith("sec"):
        seconds = 1
    elif unit.startswith("hour"):
        seconds = 3600
    else:
        seconds = 60
    return max(times, 1), seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _wait_for_db()
    await _check_llm()
    redis_url = settings.REDIS_URL
    r = None
    try:
        r = await _wait_for_redis(redis_url)
        await FastAPILimiter.init(r)
    except Exception as exc:
        structlog.get_logger().warning("redis_unavailable", error=str(exc))
        r = None
    try:
        yield
    finally:
        if r is not None:
            try:
                await FastAPILimiter.close()
            except RuntimeError:
                pass


app = FastAPI(lifespan=lifespan)

app.add_middleware(CorrelationIdMiddleware, header_name="X-Request-ID")
install_exception_handlers(app)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
origin_regex = os.getenv("CORS_ALLOW_ORIGIN_REGEX", "").strip()
allow_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() in {
    "1",
    "true",
    "yes",
}

if origins or origin_regex:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else [],
        allow_origin_regex=origin_regex if origin_regex else None,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )


_default = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
_times, _seconds = _parse_rate_limit(_default)


async def _rate_limit_dependency(request: Request, response: Response) -> None:
    if FastAPILimiter.redis:
        limiter = RateLimiter(
            times=_times, seconds=_seconds, identifier=client_ip_identifier
        )
        await limiter(request, response)


_rate_limiter_dep = Depends(_rate_limit_dependency)
app.router.dependencies.append(_rate_limiter_dep)


@app.get("/ready_db", status_code=status.HTTP_200_OK, include_in_schema=False)
async def ready_db(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """Return 200 only when migrations are at head."""
    alembic_config = os.getenv("ALEMBIC_CONFIG", "alembic.ini")
    cfg = Config(alembic_config)
    head = ScriptDirectory.from_config(cfg).get_current_head()
    result = await session.execute(sa_text("SELECT version_num FROM alembic_version"))
    current = result.scalar()
    if current == head:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="migrations pending")


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ok", "env": settings.ENV}


app.include_router(upload_router, prefix="/upload")
app.include_router(ingest_router)
app.include_router(roi_router)
app.include_router(stats_router)
app.include_router(score_router)
app.include_router(health_router.router)


async def _wait_for_db(max_attempts: int = 10, delay_s: float = 0.05) -> None:
    env = os.getenv("ENV", getattr(settings, "ENV", "local")).lower()

    # DSN precedence: ENV -> settings -> safe fallback (prevents early-return)
    db_url = (
        (os.getenv("DATABASE_URL") or "").strip()
        or str(getattr(settings, "DATABASE_URL", "")).strip()
        or "postgresql+psycopg://app:app@db:5432/app"
    )

    last_err: Exception | None = None
    for _ in range(max_attempts):
        engine = sqlalchemy.create_engine(db_url)
        try:
            with engine.connect() as conn:
                conn.execute(sa_text("SELECT 1"))
            last_err = None
            break
        except Exception as exc:
            last_err = exc
            await asyncio.sleep(delay_s)  # test monkeypatches sleep to no-op
        finally:
            try:
                engine.dispose()
            except Exception:
                pass

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

    provider = os.getenv(
        "LLM_PROVIDER", getattr(settings, "LLM_PROVIDER", "stub")
    ).lower()
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


__all__ = ["app", "ready"]
