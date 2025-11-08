from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Coroutine
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, TypeVar, cast

import httpx
import structlog
from celery import Celery, shared_task
from sqlalchemy import create_engine, text

from awa_common.dsn import build_dsn
from awa_common.logging import configure_logging
from awa_common.metrics import (
    init as metrics_init,
    instrument_task as _instrument_task,
    record_etl_batch,
    record_etl_retry,
)
from awa_common.sentry import init_sentry
from awa_common.settings import settings as SETTINGS
from awa_common.utils.env import env_str
from services.etl import http_client

from . import db_async
from .client import fetch_fees

configure_logging(service="fees_h10", level=SETTINGS.LOG_LEVEL)
metrics_init(service="fees_h10", env=SETTINGS.APP_ENV, version=SETTINGS.APP_VERSION)
init_sentry("fees_h10")

_AsyncToSyncType = Callable[[Callable[..., Awaitable[Any]]], Callable[..., Any]]


def _fallback_async_to_sync(func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        coroutine = cast(Coroutine[Any, Any, Any], func(*args, **kwargs))
        return asyncio.run(coroutine)

    return _wrapper


_async_to_sync_value: Any | None = None
try:
    from asgiref.sync import async_to_sync as _imported_async_to_sync
except ModuleNotFoundError:  # pragma: no cover - fallback when asgiref missing
    pass
else:
    _async_to_sync_value = _imported_async_to_sync

if _async_to_sync_value is None:
    async_to_sync: _AsyncToSyncType = _fallback_async_to_sync
else:
    async_to_sync = cast(_AsyncToSyncType, _async_to_sync_value)


logger = structlog.get_logger(__name__).bind(component="fees_h10")
_F = TypeVar("_F", bound=Callable[..., Any])
instrument_task = cast(Callable[[str], Callable[[_F], _F]], _instrument_task)

app = Celery("fees_h10", broker=SETTINGS.BROKER_URL or "memory://")
app.conf.beat_schedule = {"refresh-daily": {"task": "fees.refresh", "schedule": 86400.0}}


def _database_configured() -> bool:
    return bool(env_str("DATABASE_URL") or env_str("PG_ASYNC_DSN"))


def list_active_asins() -> list[str]:
    if not _database_configured():
        return []
    url = build_dsn(sync=True)
    engine = create_engine(url, future=True)
    try:
        with engine.begin() as conn:
            res = conn.execute(text("SELECT asin FROM products"))
            return [r[0] for r in res.fetchall()]
    except Exception:
        logger.warning("fees_h10.asin_lookup_failed", component="fees_h10")
        return []
    finally:
        engine.dispose()


def _quantize(value: Any) -> Decimal:
    try:
        return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")


def _normalise_row(raw: dict[str, Any]) -> dict[str, Any]:
    currency = str(raw.get("currency") or "EUR").strip().upper() or "EUR"
    currency = currency[:3]
    return {
        "asin": raw.get("asin"),
        "fulfil_fee": _quantize(raw.get("fulfil_fee")),
        "referral_fee": _quantize(raw.get("referral_fee")),
        "storage_fee": _quantize(raw.get("storage_fee")),
        "currency": currency,
    }


def _retry_reason(exc: BaseException) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        status = exc.response.status_code
        if status == 429:
            return "rate_limit"
        if 500 <= status < 600:
            return "5xx"
        return str(status)
    return exc.__class__.__name__


async def _fetch_single(asin: str, semaphore: asyncio.Semaphore) -> dict[str, Any] | None:
    async with semaphore:
        try:
            payload = await fetch_fees(asin)
        except httpx.HTTPError as exc:
            logger.warning(
                "fees_h10.fetch_failed",
                component="fees_h10",
                asin=asin,
                error=str(exc),
                error_type=exc.__class__.__name__,
            )
            record_etl_retry("fees_h10", _retry_reason(exc))
            return None
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "fees_h10.fetch_failed",
                component="fees_h10",
                asin=asin,
                error=str(exc),
                error_type=exc.__class__.__name__,
            )
            record_etl_retry("fees_h10", _retry_reason(exc))
            return None
        row = _normalise_row(payload)
        if not row["asin"]:
            logger.warning("fees_h10.missing_asin", component="fees_h10", asin=asin)
            return None
        return row


async def _bulk(asins: list[str]) -> None:
    if not asins:
        logger.info("fees_h10.no_asins", component="fees_h10")
        return

    semaphore = asyncio.Semaphore(max(1, SETTINGS.H10_MAX_CONCURRENCY))
    start = time.perf_counter()
    results = await asyncio.gather(*(_fetch_single(asin, semaphore) for asin in asins))
    rows = [row for row in results if row]
    failures = len(asins) - len(rows)

    if failures:
        logger.warning(
            "fees_h10.partial_fetch",
            component="fees_h10",
            requested=len(asins),
            successes=len(rows),
            failures=failures,
        )

    if not rows:
        record_etl_batch("fees_h10", processed=0, errors=failures, duration_s=time.perf_counter() - start)
        return

    if not _database_configured():
        logger.warning("fees_h10.database_unconfigured", component="fees_h10", pending_rows=len(rows))
        record_etl_batch("fees_h10", processed=0, errors=failures, duration_s=time.perf_counter() - start)
        return

    summary = await db_async.upsert_fee_rows(rows)
    duration_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "fees_h10.upsert_completed",
        component="fees_h10",
        requested=len(asins),
        processed=len(rows),
        inserted=summary["inserted"],
        updated=summary["updated"],
        failures=failures,
        duration_ms=duration_ms,
    )
    record_etl_batch(
        "fees_h10",
        processed=len(rows),
        errors=failures,
        duration_s=duration_ms / 1000,
    )


async def _run_refresh(asins: list[str]) -> None:
    await http_client.init_http()
    try:
        await _bulk(asins)
    finally:
        await http_client.close_http()
        await db_async.close_pool()


@shared_task(name="fees.refresh")  # type: ignore[misc]
@instrument_task("fees_h10_update")
def refresh_fees() -> None:
    asins = list_active_asins()
    async_to_sync(_run_refresh)(asins)
