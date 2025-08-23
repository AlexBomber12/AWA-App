import asyncio
import os
from contextlib import asynccontextmanager

import httpx
import redis.asyncio as aioredis
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from alembic.config import Config
from alembic.script import ScriptDirectory
from api.routers.ingest import router as ingest_router
from services.api.errors import install_exception_handlers
from services.api.logging_config import configure_logging
from services.api.sentry_config import init_sentry_if_configured
from services.common.dsn import build_dsn
from services.ingest.upload_router import router as upload_router

from .db import get_session
from .routes import health as health_router
from .routes.roi import router as roi_router
from .routes.score import router as score_router
from .routes.stats import router as stats_router

configure_logging()
init_sentry_if_configured()


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
    seconds = (
        60
        if unit.startswith("min")
        else 1
        if unit.startswith("sec")
        else 3600
        if unit.startswith("hour")
        else 60
    )
    return max(times, 1), seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _wait_for_db()
    await _check_llm()
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    r = await _wait_for_redis(redis_url)
    await FastAPILimiter.init(r)
    try:
        yield
    finally:
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
app.router.dependencies.append(
    Depends(
        RateLimiter(times=_times, seconds=_seconds, identifier=client_ip_identifier)
    )
)


@app.get("/ready", status_code=status.HTTP_200_OK, include_in_schema=False)
async def ready(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """Return 200 only when migrations are at head."""
    alembic_config = os.getenv("ALEMBIC_CONFIG", "alembic.ini")
    cfg = Config(alembic_config)
    head = ScriptDirectory.from_config(cfg).get_current_head()
    result = await session.execute(text("SELECT version_num FROM alembic_version"))
    current = result.scalar()
    if current == head:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="migrations pending")


app.include_router(upload_router, prefix="/upload")
app.include_router(ingest_router)
app.include_router(roi_router)
app.include_router(stats_router)
app.include_router(score_router)
app.include_router(health_router.router)


async def _wait_for_db() -> None:
    """Block application startup until the database becomes available."""
    from sqlalchemy import create_engine

    url = build_dsn(sync=True)

    delay = 0.2
    for _ in range(50):
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            return
        except Exception:
            await asyncio.sleep(delay)
    raise RuntimeError("Database not available")


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
    from services.common.llm import LAN_BASE, LLM_PROVIDER, LLM_PROVIDER_FALLBACK

    if LLM_PROVIDER != "lan":
        return
    try:
        async with httpx.AsyncClient(timeout=5) as cli:
            await cli.get(f"{LAN_BASE}/health")
    except Exception:
        os.environ["LLM_PROVIDER"] = LLM_PROVIDER_FALLBACK
