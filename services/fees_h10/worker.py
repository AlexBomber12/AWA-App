from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable, Coroutine
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, Any, cast

import httpx
import structlog
from celery import Celery, shared_task
from sqlalchemy import create_engine, text, update
from sqlalchemy.orm import sessionmaker

from awa_common.db.load_log import LOAD_LOG
from awa_common.dsn import build_dsn
from awa_common.etl.guard import process_once
from awa_common.etl.idempotency import build_payload_meta, compute_idempotency_key
from awa_common.logging import configure_logging
from awa_common.metrics import (
    init as metrics_init,
    instrument_task as _instrument_task,
    record_etl_batch,
    record_etl_retry,
    record_etl_run,
    record_etl_skip,
)
from awa_common.sentry import init_sentry
from awa_common.settings import settings as SETTINGS

from . import db_async
from .client import close_http_client, fetch_fees, init_http_client

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


if TYPE_CHECKING:
    from typing import Protocol, TypeVar

    _InstrumentFunc = TypeVar("_InstrumentFunc", bound=Callable[..., Any])

    class _InstrumentTaskCallable(Protocol):
        def __call__(
            self, task_name: str, *, emit_metrics: bool = True
        ) -> Callable[[_InstrumentFunc], _InstrumentFunc]: ...

    instrument_task: _InstrumentTaskCallable = _instrument_task
else:
    instrument_task = _instrument_task

logger = structlog.get_logger(__name__).bind(component="fees_h10")
SOURCE_NAME = "fees_h10"
HELIUM_ENDPOINT_PATH = "/v1/profits/fees"


def _helium_base_url() -> str:
    etl_cfg = getattr(SETTINGS, "etl", None)
    base = getattr(etl_cfg, "helium10_base_url", None) or getattr(SETTINGS, "HELIUM10_BASE_URL", "")
    return (base or "https://api.helium10.com").rstrip("/")


HELIUM_ENDPOINT = f"{_helium_base_url()}{HELIUM_ENDPOINT_PATH}"

app = Celery("fees_h10", broker=SETTINGS.BROKER_URL or "memory://")
app.conf.beat_schedule = {"refresh-daily": {"task": "fees.refresh", "schedule": 86400.0}}


def _database_configured() -> bool:
    db_cfg = getattr(SETTINGS, "db", None)
    return bool(db_cfg and db_cfg.url)


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


def build_idempotency(asins: list[str]) -> tuple[str, dict[str, Any]]:
    payload = json.dumps({"asins": sorted(asins)}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    key = compute_idempotency_key(content=payload)
    meta = build_payload_meta(
        extra={
            "asin_count": len(asins),
            "mode": "live",
            "source_url": HELIUM_ENDPOINT,
        }
    )
    return key, meta


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


async def _bulk(asins: list[str]) -> dict[str, int]:
    if not asins:
        logger.info("fees_h10.no_asins", component="fees_h10")
        return {"requested": 0, "processed": 0, "failures": 0, "inserted": 0, "updated": 0}

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
        return {"requested": len(asins), "processed": 0, "failures": failures, "inserted": 0, "updated": 0}

    if not _database_configured():
        logger.warning("fees_h10.database_unconfigured", component="fees_h10", pending_rows=len(rows))
        record_etl_batch("fees_h10", processed=0, errors=failures, duration_s=time.perf_counter() - start)
        return {"requested": len(asins), "processed": 0, "failures": failures, "inserted": 0, "updated": 0}

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
    return {
        "requested": len(asins),
        "processed": len(rows),
        "failures": failures,
        "inserted": summary.get("inserted", 0),
        "updated": summary.get("updated", 0),
    }


async def _run_refresh(asins: list[str]) -> dict[str, int]:
    await init_http_client()
    try:
        return await _bulk(asins)
    finally:
        await close_http_client()
        await db_async.close_pool()


@shared_task(name="fees.refresh")  # type: ignore[misc]
@instrument_task("fees_h10_update", emit_metrics=False)
def refresh_fees() -> None:
    asins = list_active_asins()
    idempotency_key, payload_meta = build_idempotency(asins)
    engine = create_engine(build_dsn(sync=True), future=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    summary: dict[str, int] | None = None
    try:
        with process_once(
            SessionLocal,
            source=SOURCE_NAME,
            payload_meta=payload_meta,
            idempotency_key=idempotency_key,
            on_duplicate="update_meta",
        ) as handle:
            if handle is None:
                record_etl_skip(SOURCE_NAME)
                logger.info(
                    "fees_h10.skipped",
                    idempotency_key=idempotency_key,
                    asin_count=len(asins),
                )
                return

            with record_etl_run(SOURCE_NAME):
                summary = async_to_sync(_run_refresh)(asins)
            if handle:
                meta = dict(payload_meta)
                meta.update(summary or {})
                handle.session.execute(
                    update(LOAD_LOG).where(LOAD_LOG.c.id == handle.load_log_id).values(payload_meta=meta)
                )
    finally:
        engine.dispose()
