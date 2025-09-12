from __future__ import annotations

import os
from typing import Any, List

from celery.utils.log import get_task_logger
from sqlalchemy import create_engine, text

from packages.awa_common.dsn import build_dsn

from .celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="ingest.analyze_table")  # type: ignore[misc]
def task_analyze_table(table_fqname: str) -> dict[str, str]:
    engine = create_engine(build_dsn(sync=True))
    try:
        with engine.begin() as conn:
            conn.execute(text(f"ANALYZE {table_fqname}"))
        return {"status": "success", "table": table_fqname}
    finally:
        engine.dispose()


@celery_app.task(name="ingest.maintenance_nightly")  # type: ignore[misc]
def task_maintenance_nightly() -> dict[str, Any]:
    tables_cfg = os.getenv(
        "TABLE_MAINTENANCE_LIST", "public.reimbursements_raw,public.returns_raw"
    )
    tables: List[str] = [t.strip() for t in tables_cfg.split(",") if t.strip()]
    vacuum = os.getenv("VACUUM_ENABLE", "false").lower() in ("1", "true", "yes")
    engine = create_engine(build_dsn(sync=True))
    processed: List[str] = []
    try:
        with engine.begin() as conn:
            for tbl in tables:
                stmt = f"VACUUM ANALYZE {tbl}" if vacuum else f"ANALYZE {tbl}"
                conn.execute(text(stmt))
                processed.append(tbl)
        return {"status": "success", "tables": processed}
    finally:
        engine.dispose()
