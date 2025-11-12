from __future__ import annotations

import argparse
import asyncio
import hashlib
import time
from typing import TYPE_CHECKING, Any

import anyio
import structlog

from awa_common.metrics import (
    instrument_task as _instrument_task,
    logistics_task_inflight_change,
    record_etl_batch,
    record_etl_retry,
    record_etl_run,
    record_logistics_error,
    record_logistics_rows,
    record_logistics_task_duration,
)
from awa_common.settings import Settings

from . import client, repository

logger = structlog.get_logger(__name__).bind(component="logistics_etl")

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Protocol, TypeVar

    _InstrumentFunc = TypeVar("_InstrumentFunc", bound=Callable[..., Any])

    class _InstrumentTaskCallable(Protocol):
        def __call__(
            self, task_name: str, *, emit_metrics: bool = True
        ) -> Callable[[_InstrumentFunc], _InstrumentFunc]: ...

    instrument_task: _InstrumentTaskCallable = _instrument_task
else:
    instrument_task = _instrument_task


@instrument_task("logistics_etl")
async def full(dry_run: bool = False) -> list[dict[str, Any]]:
    cfg = Settings()
    sources_config = (cfg.LOGISTICS_SOURCES or "").strip()
    with record_etl_run("logistics_etl"):
        snapshots = await client.fetch_sources()
        if snapshots:
            return await _process_snapshots(
                snapshots,
                dry_run=dry_run,
                per_source_timeout=max(1, int(cfg.LOGISTICS_PER_SOURCE_TIMEOUT_SECONDS)),
                gather_timeout=max(1, int(cfg.LOGISTICS_GATHER_TIMEOUT_SECONDS)),
                max_concurrency=max(1, int(cfg.LOGISTICS_MAX_CONCURRENCY)),
            )

    if sources_config:
        return []

    legacy_rows: list[dict[str, Any]] = await client.fetch_rates()
    if dry_run or not legacy_rows:
        return legacy_rows

    await repository.upsert_many(
        table="logistics_rates",
        key_cols=["carrier", "origin", "dest", "service", "effective_from"],
        rows=legacy_rows,
        update_columns=["eur_per_kg", "effective_to", "updated_at"],
    )
    return legacy_rows


async def _process_snapshots(
    snapshots: list[dict[str, Any]],
    *,
    dry_run: bool,
    per_source_timeout: int,
    gather_timeout: int,
    max_concurrency: int,
) -> list[dict[str, Any]]:
    sem = asyncio.Semaphore(max_concurrency)
    results: list[dict[str, Any] | None] = [None] * len(snapshots)

    async def _run_single(idx: int, snapshot: dict[str, Any]) -> None:
        uri = str(snapshot.get("source") or "unknown")
        start = time.perf_counter()
        async with sem:
            logistics_task_inflight_change(uri, 1)
            try:
                with anyio.fail_after(per_source_timeout):
                    summary = await _handle_snapshot(snapshot, dry_run=dry_run)
            except TimeoutError:
                record_logistics_error(uri, "timeout")
                record_etl_retry("logistics_etl", "timeout")
                logger.warning("logistics_etl.timeout", source=uri, timeout_s=per_source_timeout)
                summary = _timeout_result(snapshot)
            except asyncio.CancelledError:  # pragma: no cover - cooperative shutdown
                record_logistics_error(uri, "cancelled")
                record_etl_retry("logistics_etl", "cancelled")
                logger.warning("logistics_etl.cancelled", source=uri)
                raise
            except Exception as exc:
                record_logistics_error(uri, exc.__class__.__name__)
                record_etl_retry("logistics_etl", exc.__class__.__name__)
                logger.exception("logistics_etl.failed", source=uri, error=str(exc))
                summary = _error_result(snapshot, exc)
            finally:
                duration = time.perf_counter() - start
                record_logistics_task_duration(uri, duration)
                logistics_task_inflight_change(uri, -1)

        _record_snapshot_metrics(summary, dry_run=dry_run, duration=duration)
        results[idx] = summary

    async def _runner() -> None:
        async with anyio.create_task_group() as tg:
            for idx, snapshot in enumerate(snapshots):
                tg.start_soon(_run_single, idx, snapshot)

    try:
        await asyncio.wait_for(_runner(), timeout=gather_timeout)
    except TimeoutError:
        logger.error("logistics_etl.gather_timeout", timeout_s=gather_timeout, sources=len(snapshots))
        raise

    return [res for res in results if res is not None]


async def _handle_snapshot(snapshot: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    uri = str(snapshot.get("source") or "unknown")
    raw, meta, rows = _hydrate_snapshot(snapshot)
    error = snapshot.get("error")
    if isinstance(error, BaseException):
        raise error
    sha256 = hashlib.sha256(raw).hexdigest() if raw else None
    seqno_value = meta.get("seqno")
    seqno = str(seqno_value) if seqno_value is not None else None
    logical_source = str(meta.get("source") or uri)

    skipped = False
    rows_upserted = 0
    if sha256 or seqno:
        already_seen = await repository.seen_load(logical_source, sha256, seqno)
        if already_seen:
            skipped = True

    if not skipped and not dry_run and rows:
        db_rows = [
            {
                "carrier": row["carrier"],
                "origin": row["origin"],
                "dest": row["dest"],
                "service": row["service"],
                "eur_per_kg": row["eur_per_kg"],
                "effective_from": row["valid_from"],
                "effective_to": row["valid_to"],
                "source": row.get("source"),
            }
            for row in rows
        ]
        summary = await repository.upsert_many(
            table="logistics_rates",
            key_cols=["carrier", "origin", "dest", "service", "effective_from"],
            rows=db_rows,
            update_columns=["eur_per_kg", "effective_to", "updated_at"],
        )
        rows_upserted = (summary or {}).get("inserted", 0) + (summary or {}).get("updated", 0)
        if sha256 is not None or seqno is not None:
            await repository.mark_load(logical_source, sha256, seqno, len(rows))

    status = "success"
    if skipped:
        status = "skipped"

    return {
        "source": uri,
        "rows_in": len(rows),
        "rows_upserted": rows_upserted if not dry_run and not skipped else 0,
        "skipped": skipped,
        "sha256": sha256,
        "seqno": seqno,
        "status": status,
    }


def _hydrate_snapshot(snapshot: dict[str, Any]) -> tuple[bytes, dict[str, Any], list[dict[str, Any]]]:
    raw_value = snapshot.get("raw")
    if isinstance(raw_value, bytearray):
        raw = bytes(raw_value)
    elif isinstance(raw_value, bytes):
        raw = raw_value
    else:
        raw = b""

    meta_value = snapshot.get("meta")
    meta = meta_value if isinstance(meta_value, dict) else {}

    rows_value = snapshot.get("rows")
    if isinstance(rows_value, list):
        rows = rows_value
    elif rows_value:
        try:
            rows = list(rows_value)
        except TypeError:
            rows = []
    else:
        rows = []
    return raw, meta, rows


def _timeout_result(snapshot: dict[str, Any]) -> dict[str, Any]:
    uri = str(snapshot.get("source") or "unknown")
    _, meta, rows = _hydrate_snapshot(snapshot)
    return {
        "source": uri,
        "rows_in": len(rows),
        "rows_upserted": 0,
        "skipped": False,
        "sha256": None,
        "seqno": meta.get("seqno"),
        "status": "timeout",
    }


def _error_result(snapshot: dict[str, Any], exc: Exception) -> dict[str, Any]:
    uri = str(snapshot.get("source") or "unknown")
    _, meta, rows = _hydrate_snapshot(snapshot)
    return {
        "source": uri,
        "rows_in": len(rows),
        "rows_upserted": 0,
        "skipped": False,
        "sha256": None,
        "seqno": meta.get("seqno"),
        "status": f"error:{exc.__class__.__name__}",
    }


def _record_snapshot_metrics(summary: dict[str, Any], *, dry_run: bool, duration: float) -> None:
    status = summary.get("status") or "unknown"
    skipped = summary.get("skipped", False)
    rows_processed = int(summary.get("rows_upserted") or 0)
    rows_in = int(summary.get("rows_in") or 0)
    source = summary.get("source") or "unknown"

    if not dry_run:
        if skipped:
            record_logistics_rows(source, rows=rows_in, result="skipped")
        elif status == "success":
            record_logistics_rows(source, rows=rows_processed, result="processed")

    record_etl_batch(
        "logistics_etl",
        processed=0 if dry_run or skipped or status != "success" else rows_processed,
        errors=0 if status in {"success", "skipped"} else 1,
        duration_s=max(duration, 0.0),
    )


def _sync_full(dry_run: bool = False) -> list[dict[str, Any]]:
    return asyncio.run(full(dry_run=dry_run))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(full(dry_run=args.dry_run))
