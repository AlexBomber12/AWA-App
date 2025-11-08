from __future__ import annotations

import argparse
import time
from pathlib import Path

import structlog

from awa_common.logging import configure_logging
from awa_common.settings import settings as SETTINGS

from .io import DEFAULT_BATCH_SIZE, iter_price_batches
from .repository import Repository

logger = structlog.get_logger(__name__)


def _ensure_logging() -> None:
    configure_logging(
        service="price_importer",
        env=SETTINGS.APP_ENV,
        version=SETTINGS.APP_VERSION,
        level=SETTINGS.LOG_LEVEL,
    )


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

    _ensure_logging()
    repo = Repository()
    vendor_id = repo.ensure_vendor(args.vendor)
    file_name = Path(args.file).name
    total_inserted = 0
    total_updated = 0
    total_processed = 0
    start_time = time.perf_counter()

    try:
        for batch_no, batch in enumerate(iter_price_batches(args.file, batch_size=args.batch_size), start=1):
            batch_start = time.perf_counter()
            inserted, updated = repo.upsert_prices(vendor_id, batch, dry_run=args.dry_run)
            batch_count = len(batch)
            total_inserted += inserted
            total_updated += updated
            total_processed += batch_count
            logger.info(
                "price_import.batch_completed",
                component="price_importer",
                vendor=args.vendor,
                vendor_id=vendor_id,
                file_name=file_name,
                batch_number=batch_no,
                batch_size=batch_count,
                inserted=inserted,
                updated=updated,
                total_processed=total_processed,
                duration_ms=int((time.perf_counter() - batch_start) * 1000),
                dry_run=args.dry_run,
            )
    except ValueError as exc:
        logger.error(
            "price_import.validation_failed",
            component="price_importer",
            vendor=args.vendor,
            vendor_id=vendor_id,
            file_name=file_name,
            error=str(exc),
        )
        raise

    logger.info(
        "price_import.completed",
        component="price_importer",
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
