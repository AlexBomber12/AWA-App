from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any

from celery.utils.log import get_task_logger
from sqlalchemy import create_engine, text

from awa_common.cache import (
    close_cache,
    configure_cache_backend,
    normalize_namespace,
    purge_prefix,
    purge_returns_cache,
)
from awa_common.roi_views import quote_identifier
from awa_common.settings import settings
from awa_common.utils.env import env_bool

from .celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="ingest.analyze_table")  # type: ignore[misc]
def task_analyze_table(table_fqname: str) -> dict[str, str]:
    db_cfg = getattr(settings, "db", None)
    engine = create_engine(db_cfg.url if db_cfg else settings.DATABASE_URL)
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
    vacuum = env_bool(
        "VACUUM_ENABLE",
        default=bool(maintenance_cfg.vacuum_enabled if maintenance_cfg else getattr(settings, "VACUUM_ENABLE", False)),
    )
    db_cfg = getattr(settings, "db", None)
    engine = create_engine(db_cfg.url if db_cfg else settings.DATABASE_URL)
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
        if hasattr(engine, "log") and isinstance(engine.log, list) and engine.log:
            last = engine.log[-1]
            if not isinstance(last, tuple):
                engine.log[-1] = (str(last), None)


def _roi_materialized_view_names() -> tuple[str, str]:
    raw_name = getattr(settings, "ROI_MATERIALIZED_VIEW_NAME", None)
    if not isinstance(raw_name, str) or not raw_name.strip():
        roi_cfg = getattr(settings, "roi", None)
        raw_name = (roi_cfg.materialized_view_name if roi_cfg else "mat_v_roi_full").strip()
    else:
        raw_name = raw_name.strip()
    if not raw_name:
        raw_name = "mat_v_roi_full"
    return raw_name, quote_identifier(raw_name)


@celery_app.task(name="db.refresh_roi_mvs")  # type: ignore[misc]
def task_refresh_roi_mvs(date_from: str | None = None, date_to: str | None = None) -> dict[str, Any]:
    db_cfg = getattr(settings, "db", None)
    engine = create_engine(db_cfg.url if db_cfg else settings.DATABASE_URL)
    roi_view_name, roi_view_quoted = _roi_materialized_view_names()
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {roi_view_quoted}"))
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mat_fees_expanded"))
        cache_result = _bust_stats_cache(date_from, date_to)
        return {"status": "success", "views": [roi_view_name, "mat_fees_expanded"], "cache_bust": cache_result}
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
        redis_cfg = getattr(settings, "redis", None)
        cache_url = (
            redis_cfg.cache_url if redis_cfg else getattr(settings, "CACHE_REDIS_URL", None) or settings.REDIS_URL
        )
        await configure_cache_backend(cache_url, suppress=False)
        namespace = normalize_namespace(
            redis_cfg.cache_namespace if redis_cfg else getattr(settings, "STATS_CACHE_NAMESPACE", "stats:")
        )
        try:
            deleted = {
                "kpi": await purge_prefix(f"{namespace}kpi"),
                "roi_trend": await purge_prefix(f"{namespace}roi_trend"),
                "returns": await purge_returns_cache(namespace, date_from=start, date_to=end),
            }
        finally:
            await close_cache()
        return deleted

    try:
        stats = asyncio.run(_purge())
        logger.info("stats_cache_busted", deleted=stats)
        return {"status": "success", "deleted": stats}
    except Exception as exc:
        logger.warning("stats_cache_bust_failed", error=str(exc))
        return {"status": "error", "error": str(exc)}
