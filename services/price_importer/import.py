from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from awa_common.db.load_log import LOAD_LOG
from awa_common.etl.guard import process_once
from awa_common.etl.idempotency import build_payload_meta, compute_idempotency_key
from awa_common.logging import configure_logging
from awa_common.metrics import (
    flush_textfile,
    init as metrics_init,
    instrument_task as _instrument_task,
    record_etl_batch,
    record_etl_run,
    record_etl_skip,
)
from awa_common.sentry import init_sentry
from awa_common.settings import settings as SETTINGS

from .io import DEFAULT_BATCH_SIZE, iter_price_batches
from .repository import Repository

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

logger = structlog.get_logger(__name__).bind(component="price_importer")
SOURCE_NAME = "price_import"


def _bootstrap_observability() -> None:
    configure_logging(service="price_importer", level=SETTINGS.LOG_LEVEL)
    metrics_init(service="price_importer", env=SETTINGS.APP_ENV, version=SETTINGS.APP_VERSION)
    init_sentry("price_importer")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import vendor price sheet")
    parser.add_argument("file")
    parser.add_argument("--vendor", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Rows per batch transaction (default: {DEFAULT_BATCH_SIZE})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    _bootstrap_observability()
    status = asyncio.run(_run_import(args))
    flush_textfile("price_importer")
    return status


@instrument_task("price_import")
async def _run_import(args: argparse.Namespace) -> int:
    repo = Repository()
    vendor_id = repo.ensure_vendor(args.vendor)
    file_path = Path(args.file)
    payload_meta = build_payload_meta(
        path=file_path,
        extra={"vendor": args.vendor, "batch_size": args.batch_size, "dry_run": args.dry_run},
    )
    file_hash = None
    if file_path.exists():
        try:
            file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        except OSError:
            file_hash = None
    key_seed = json.dumps(
        {
            "vendor_id": vendor_id,
            "file": file_path.name,
            "size": file_path.stat().st_size if file_path.exists() else None,
            "sha256": file_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    idempotency_key = compute_idempotency_key(content=key_seed)
    engine = getattr(repo, "engine", None)

    def _fallback_session_factory() -> Any:
        class _DummyResult:
            def __init__(self, inserted: bool = True) -> None:
                self.inserted = inserted

            def scalar_one_or_none(self) -> int | None:
                return 1 if self.inserted else None

        class _DummySession:
            def __init__(self) -> None:
                self._result = _DummyResult()

            def execute(self, *_a: Any, **_k: Any) -> _DummyResult:
                return self._result

            def flush(self) -> None:
                return None

            def commit(self) -> None:
                return None

            def rollback(self) -> None:
                return None

            def close(self) -> None:
                return None

        return _DummySession()

    if engine is None:
        SessionLocal = _fallback_session_factory
    else:
        try:
            SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        except Exception:
            SessionLocal = _fallback_session_factory
    file_name = Path(args.file).name
    total_inserted = 0
    total_updated = 0
    total_processed = 0
    start_time = time.perf_counter()

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
                "price_import.skipped",
                idempotency_key=idempotency_key,
                vendor=args.vendor,
                file_name=file_name,
            )
            return 0

        with record_etl_run(SOURCE_NAME):
            try:
                batch_no = 0
                batches_iter = iter_price_batches(args.file, batch_size=args.batch_size)
                if inspect.isawaitable(batches_iter) and not hasattr(batches_iter, "__aiter__"):
                    batches_iter = await batches_iter  # may raise ValueError for bad inputs
                async for batch in batches_iter:
                    batch_no += 1
                    batch_start = time.perf_counter()
                    inserted, updated = repo.upsert_prices(vendor_id, batch, dry_run=args.dry_run)
                    batch_count = len(batch)
                    total_inserted += inserted
                    total_updated += updated
                    total_processed += batch_count
                    duration_s = time.perf_counter() - batch_start
                    record_etl_batch(
                        "price_import",
                        processed=batch_count,
                        errors=0,
                        duration_s=duration_s,
                    )
                    logger.info(
                        "price_import.batch_completed",
                        vendor=args.vendor,
                        vendor_id=vendor_id,
                        file_name=file_name,
                        batch_number=batch_no,
                        batch_size=batch_count,
                        inserted=inserted,
                        updated=updated,
                        total_processed=total_processed,
                        duration_ms=int(duration_s * 1000),
                        dry_run=args.dry_run,
                    )
            except ValueError as exc:
                record_etl_batch(
                    "price_import",
                    processed=0,
                    errors=1,
                    duration_s=time.perf_counter() - start_time,
                )
                logger.error(
                    "price_import.validation_failed",
                    vendor=args.vendor,
                    vendor_id=vendor_id,
                    file_name=file_name,
                    error=str(exc),
                )
                raise
        if handle:
            meta = dict(payload_meta)
            meta.update(
                {
                    "inserted": total_inserted,
                    "updated": total_updated,
                    "processed": total_processed,
                    "vendor_id": vendor_id,
                }
            )
            handle.session.execute(
                update(LOAD_LOG).where(LOAD_LOG.c.id == handle.load_log_id).values(payload_meta=meta)
            )

    logger.info(
        "price_import.completed",
        vendor=args.vendor,
        vendor_id=vendor_id,
        file_name=file_name,
        inserted=total_inserted,
        updated=total_updated,
        total_processed=total_processed,
        duration_ms=int((time.perf_counter() - start_time) * 1000),
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
