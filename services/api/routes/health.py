from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis
import sentry_sdk
import structlog
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.db.async_session import get_async_session
from awa_common.metrics import record_redis_error
from awa_common.settings import settings

MAX_SKEW = 30  # seconds

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health", include_in_schema=False)  # type: ignore[misc]
async def health(request: Request, session: AsyncSession = Depends(get_async_session)) -> JSONResponse:
    """Return 200 when DB reachable and clocks are in sync."""
    result = await session.execute(text("SELECT (now() AT TIME ZONE 'UTC')"))
    db_now = result.scalar()
    if isinstance(db_now, datetime):
        db_now = db_now.replace(tzinfo=UTC)
    app_now = datetime.now(UTC)
    redis_snapshot = await _redis_health_snapshot(request)
    if db_now is None or abs((db_now - app_now).total_seconds()) > MAX_SKEW:
        payload = {
            "detail": "clock_skew",
            "database": {"status": "error", "detail": "clock_skew"},
            "redis": redis_snapshot,
        }
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)
    payload: dict[str, Any] = {
        "status": "ok",
        "database": {"status": "ok"},
        "redis": redis_snapshot,
    }
    status_code = status.HTTP_200_OK
    redis_status = redis_snapshot.get("status")
    if redis_snapshot.get("critical") and redis_status == "down":
        payload["status"] = "error"
        payload["detail"] = "redis_unavailable"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif redis_status == "degraded":
        payload["status"] = "degraded"
    return JSONResponse(status_code=status_code, content=payload)


async def _redis_health_snapshot(request: Request | None) -> dict[str, Any]:
    state = getattr(getattr(request, "app", None), "state", None) if request is not None else None
    default_critical = bool(getattr(settings, "REDIS_HEALTH_CRITICAL", False))
    current = getattr(state, "redis_health", None) if state is not None else None
    if isinstance(current, dict):
        critical = bool(current.get("critical", default_critical))
    else:
        critical = default_critical
    clients: list[tuple[str, Any]] = []
    if state is not None:
        stats_cache = getattr(state, "stats_cache", None)
        if stats_cache is not None:
            clients.append(("stats_cache", stats_cache))
        limiter_client = getattr(state, "limiter_redis", None) or getattr(FastAPILimiter, "redis", None)
        if limiter_client is not None:
            clients.append(("rate_limit", limiter_client))
    if not clients and not critical:
        snapshot = {
            "status": current.get("status", "ok") if isinstance(current, dict) else "ok",
            "critical": critical,
        }
        if isinstance(current, dict) and current.get("error"):
            snapshot["error"] = current["error"]
        _update_state_snapshot(state, snapshot)
        return snapshot
    probe: aioredis.Redis | None = None
    if not clients and state is not None:
        redis_url = getattr(state, "redis_url", None) or getattr(settings, "REDIS_URL", None)
        if redis_url:
            try:
                probe = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
                clients.append(("probe", probe))
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("redis_probe_failed", error=str(exc))
                record_redis_error("health", "connect", key="probe")
                sentry_sdk.capture_exception(exc)
    last_error: str | None = None
    failures: list[tuple[str, str]] = []
    successes = 0
    for source, client in clients:
        try:
            await client.ping()
            successes += 1
        except Exception as exc:
            last_error = str(exc)
            logger.error("redis_health_ping_failed", source=source, error=str(exc))
            record_redis_error("health", "ping", key=source)
            sentry_sdk.capture_exception(exc)
            failures.append((source, last_error or "error"))
    if probe is not None:
        await probe.aclose()
    if successes == len(clients) and successes > 0:
        snapshot = {"status": "ok", "critical": critical}
        _update_state_snapshot(state, snapshot)
        return snapshot
    degraded_status = "down" if critical else "degraded"
    snapshot = {"status": degraded_status, "critical": critical}
    if failures:
        snapshot["error"] = ", ".join(f"{source}:{error}" for source, error in failures)
    elif last_error:
        snapshot["error"] = last_error
    _update_state_snapshot(state, snapshot)
    return snapshot


def _update_state_snapshot(state, snapshot: dict[str, Any]) -> None:
    if state is None:
        return
    try:
        health = getattr(state, "redis_health", None)
        if isinstance(health, dict):
            health.update({k: snapshot[k] for k in ("status", "error") if k in snapshot})
    except Exception:
        pass
