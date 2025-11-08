from __future__ import annotations

import argparse
import asyncio
import hashlib
import time
from typing import TYPE_CHECKING, Any

import structlog

from awa_common.metrics import instrument_task as _instrument_task, record_etl_batch, record_etl_retry, record_etl_run
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
async def full(dry_run: bool = False) -> list[dict[str, Any]]:  # noqa: C901
    sources_config = (Settings().LOGISTICS_SOURCES or "").strip()
    with record_etl_run("logistics_etl"):
        snapshots = await client.fetch_sources()

        if snapshots:
            results: list[dict[str, Any]] = []
            for snapshot in snapshots:
                uri_value = snapshot.get("source")
                uri = str(uri_value) if uri_value is not None else "unknown"

                raw_value = snapshot.get("raw")
                has_raw = isinstance(raw_value, (bytes, bytearray))
                if isinstance(raw_value, bytearray):
                    raw = bytes(raw_value)
                elif isinstance(raw_value, bytes):
                    raw = raw_value
                else:
                    raw = b""

                meta_value = snapshot.get("meta")
                meta: dict[str, Any] = meta_value if isinstance(meta_value, dict) else {}
                rows_value = snapshot.get("rows")
                rows: list[dict[str, Any]]
                if isinstance(rows_value, list):
                    rows = rows_value
                elif rows_value:
                    try:
                        rows = list(rows_value)
                    except TypeError:
                        rows = []
                else:
                    rows = []

                error = snapshot.get("error")
                sha256: str | None = hashlib.sha256(raw).hexdigest() if has_raw else None
                seqno_value = meta.get("seqno")
                seqno: str | None = str(seqno_value) if seqno_value is not None else None
                src_any = meta.get("source")
                src: str = str(src_any or uri)

                status = "success"
                skipped = False
                rows_upserted = 0
                start = time.monotonic()

                try:
                    if error:
                        raise error

                    already_seen = await repository.seen_load(src, sha256, seqno)
                    if already_seen:
                        skipped = True
                    else:
                        if not dry_run:
                            summary = None
                            if rows:
                                summary = await repository.upsert_many(
                                    table="logistics_rates",
                                    key_cols=[
                                        "carrier",
                                        "origin",
                                        "dest",
                                        "service",
                                        "effective_from",
                                    ],
                                    rows=rows,
                                    update_columns=[
                                        "eur_per_kg",
                                        "effective_to",
                                        "updated_at",
                                    ],
                                )
                            rows_upserted = (summary or {}).get("inserted", 0) + (summary or {}).get("updated", 0)
                            if sha256 is not None or seqno is not None:
                                await repository.mark_load(src, sha256, seqno, len(rows))
                except Exception as exc:
                    status = "failure"
                    skipped = False
                    rows_upserted = 0
                    record_etl_retry("logistics_etl", exc.__class__.__name__)
                    logger.exception("logistics_etl.failed", source=uri, error=str(exc))

                duration = time.monotonic() - start
                status_label = "skipped" if skipped else status
                record_etl_batch(
                    "logistics_etl",
                    processed=0 if skipped or dry_run else rows_upserted,
                    errors=0 if status_label == "success" else 1,
                    duration_s=duration,
                )

                results.append(
                    {
                        "source": uri,
                        "rows_in": len(rows),
                        "rows_upserted": (0 if skipped or dry_run or status != "success" else rows_upserted),
                        "skipped": skipped,
                        "sha256": sha256,
                        "seqno": seqno,
                        "status": status_label,
                    }
                )
            return results

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


def _sync_full(dry_run: bool = False) -> list[dict[str, Any]]:
    return asyncio.run(full(dry_run=dry_run))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(full(dry_run=args.dry_run))
