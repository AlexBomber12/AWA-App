from __future__ import annotations

import asyncio
import datetime as dt
import os
from typing import Any

import redis.asyncio as aioredis
from celery.utils.log import get_task_logger
from sqlalchemy import create_engine, text

from awa_common.cache import normalize_namespace, purge_prefix, purge_returns_cache
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
    maintenance_cfg = getattr(settings, "maintenance", None)
    if maintenance_cfg and maintenance_cfg.table_list:
        tables = maintenance_cfg.table_list
    else:
        tables = [
            tbl.strip()
            for tbl in (settings.TABLE_MAINTENANCE_LIST or "public.reimbursements_raw,public.returns_raw").split(",")
            if tbl.strip()
        ]
    vacuum_env = os.getenv("VACUUM_ENABLE")
    if vacuum_env is not None:
        vacuum = vacuum_env.lower() in {"1", "true", "yes"}
    else:
        vacuum = bool(maintenance_cfg.vacuum_enabled if maintenance_cfg else False)
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
def task_refresh_roi_mvs(date_from: str | None = None, date_to: str | None = None) -> dict[str, Any]:
    engine = create_engine(settings.DATABASE_URL)
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mat_v_roi_full"))
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mat_fees_expanded"))
        cache_result = _bust_stats_cache(date_from, date_to)
        return {"status": "success", "views": ["mat_v_roi_full", "mat_fees_expanded"], "cache_bust": cache_result}
    finally:
        engine.dispose()


def _parse_refresh_boundary(value: str | None) -> dt.date | None:
    if not value:
        return None
    return dt.date.fromisoformat(value)


def _bust_stats_cache(date_from: str | None, date_to: str | None) -> dict[str, Any]:
    if not getattr(settings, "STATS_ENABLE_CACHE", False):
        return {"status": "skipped"}

    try:
        start = _parse_refresh_boundary(date_from)
        end = _parse_refresh_boundary(date_to)
    except ValueError as exc:
        start = end = None
        logger.warning("stats_cache_window_parse_failed", error=str(exc))

    async def _purge() -> dict[str, int]:
        client = aioredis.from_url(  # type: ignore[no-untyped-call]
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        namespace = normalize_namespace(getattr(settings, "STATS_CACHE_NAMESPACE", "stats:"))
        try:
            deleted = {
                "kpi": await purge_prefix(client, f"{namespace}kpi"),
                "roi_trend": await purge_prefix(client, f"{namespace}roi_trend"),
                "returns": await purge_returns_cache(client, namespace, date_from=start, date_to=end),
            }
        finally:
            await client.aclose()
        return deleted

    try:
        stats = asyncio.run(_purge())
        logger.info("stats_cache_busted", deleted=stats)
        return {"status": "success", "deleted": stats}
    except Exception as exc:
        logger.warning("stats_cache_bust_failed", error=str(exc))
        return {"status": "error", "error": str(exc)}
