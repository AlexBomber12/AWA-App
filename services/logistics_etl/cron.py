from __future__ import annotations

import logging
from typing import Any

from services.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_full_sync(dry_run: bool = False) -> list[dict[str, Any]]:
    import asyncio

    from . import flow

    return asyncio.run(flow.full(dry_run=dry_run))


@celery_app.task(name="logistics.etl.full")  # type: ignore[misc]
def logistics_etl_full() -> list[dict[str, Any]]:
    """Celery task entrypoint triggered by beat."""
    try:
        return _run_full_sync(dry_run=False)
    except Exception:  # pragma: no cover - let Celery handle retry/logging
        logger.exception("Logistics ETL task failed")
        raise


def start() -> None:
    """Manual entrypoint used by __main__ for ad-hoc runs."""
    _run_full_sync(dry_run=False)
