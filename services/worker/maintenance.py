from __future__ import annotations

import os
from typing import Any

from celery.utils.log import get_task_logger
from sqlalchemy import create_engine, text

from awa_common.settings import settings

from .celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="ingest.analyze_table")  # type: ignore[misc]
def task_analyze_table(table_fqname: str) -> dict[str, str]:
    engine = create_engine(settings.DATABASE_URL)
    try:
        with engine.begin() as conn:
            conn.execute(text(f"ANALYZE {table_fqname}"))
        return {"status": "success", "table": table_fqname}
    finally:
        engine.dispose()


@celery_app.task(name="ingest.maintenance_nightly")  # type: ignore[misc]
def task_maintenance_nightly() -> dict[str, Any]:
    tables_cfg = os.getenv("TABLE_MAINTENANCE_LIST", "public.reimbursements_raw,public.returns_raw")
    tables: list[str] = [t.strip() for t in tables_cfg.split(",") if t.strip()]
    vacuum = os.getenv("VACUUM_ENABLE", "false").lower() in ("1", "true", "yes")
    engine = create_engine(settings.DATABASE_URL)
    processed: list[str] = []
    try:
        with engine.begin() as conn:
            for tbl in tables:
                stmt = f"VACUUM ANALYZE {tbl}" if vacuum else f"ANALYZE {tbl}"
                conn.execute(text(stmt))
                processed.append(tbl)
        return {"status": "success", "tables": processed}
    finally:
        engine.dispose()


@celery_app.task(name="db.refresh_roi_mvs")  # type: ignore[misc]
def task_refresh_roi_mvs() -> dict[str, Any]:
    engine = create_engine(settings.DATABASE_URL)
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mat_v_roi_full"))
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mat_fees_expanded"))
        return {"status": "success", "views": ["mat_v_roi_full", "mat_fees_expanded"]}
    finally:
        engine.dispose()
