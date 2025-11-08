from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import time
from typing import Any

from awa_common.settings import Settings

from . import client, metrics, repository

logger = logging.getLogger(__name__)


async def full(dry_run: bool = False) -> list[dict[str, Any]]:  # noqa: C901
    sources_config = (Settings().LOGISTICS_SOURCES or "").strip()
    snapshots = await client.fetch_sources()

    if snapshots:
        results: list[dict[str, Any]] = []
        for snapshot in snapshots:
            uri_value = snapshot.get("source")
            uri = str(uri_value) if uri_value is not None else "unknown"

            raw_value = snapshot.get("raw")
            has_raw = isinstance(raw_value, bytes | bytearray)
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
                metrics.etl_failures_total.labels(source=uri or "unknown", reason=exc.__class__.__name__).inc()
                logger.exception("Logistics ETL failed for %s", uri)

            duration = time.monotonic() - start
            status_label = "skipped" if skipped else status
            metrics.etl_runs_total.labels(source=uri or "unknown", status=status_label).inc()
            metrics.etl_latency_seconds.labels(source=uri or "unknown").observe(duration)

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
    print(_sync_full(dry_run=args.dry_run))
