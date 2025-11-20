from __future__ import annotations

import os
from collections.abc import Callable
from typing import Final

import structlog
from cachetools import TTLCache
from sqlalchemy import Column, MetaData, String, Table, select
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.roi_views import (
    InvalidROIViewError,
    clear_caches as clear_roi_cache,
    current_roi_view,
    quote_identifier,
)
from awa_common.settings import settings

logger = structlog.get_logger(__name__)

ROI_CACHE_TTL_ENV = "ROI_CACHE_TTL_SECONDS"
DEFAULT_CACHE_TTL_SECONDS: Final[float] = 300.0
_CACHE_SIZE: Final[int] = 128

_metadata = MetaData()
_returns_columns = Table(
    "columns",
    _metadata,
    Column("table_schema", String),
    Column("table_name", String),
    Column("column_name", String),
    schema="information_schema",
)


def _ttl_seconds() -> float:
    env_override = os.getenv(ROI_CACHE_TTL_ENV)
    if env_override:
        try:
            value = float(env_override)
        except ValueError:
            value = DEFAULT_CACHE_TTL_SECONDS
    else:
        stats_cfg = getattr(settings, "stats", None)
        value = float(stats_cfg.cache_ttl_s if stats_cfg else DEFAULT_CACHE_TTL_SECONDS)
    return value if value > 0 else DEFAULT_CACHE_TTL_SECONDS


def _new_vendor_cache() -> TTLCache[str, bool]:
    return TTLCache(maxsize=_CACHE_SIZE, ttl=_ttl_seconds())


_returns_vendor_cache = _new_vendor_cache()


def get_roi_view_name() -> str:
    """Return the configured ROI view name."""
    resolver: Callable[[], str] = current_roi_view
    return resolver()


def get_quoted_roi_view() -> str:
    """Return the configured ROI view name quoted for SQL usage."""
    formatter: Callable[[str], str] = quote_identifier
    return formatter(get_roi_view_name())


async def returns_vendor_column_exists(
    session: AsyncSession,
    *,
    table_name: str = "returns_raw",
    schema: str = "public",
) -> bool:
    """Return True if returns_raw.vendor exists while caching the discovery."""
    key = f"{schema}.{table_name}".lower()
    cached = _returns_vendor_cache.get(key)
    if isinstance(cached, bool):
        return cached
    stmt = (
        select(_returns_columns.c.column_name)
        .where(
            (_returns_columns.c.table_schema == schema)
            & (_returns_columns.c.table_name == table_name)
            & (_returns_columns.c.column_name == "vendor")
        )
        .limit(1)
    )
    try:
        result = await session.execute(stmt)
        found = result.scalar() is not None
    except Exception as exc:
        logger.warning(
            "returns.vendor_column_check_failed",
            schema=schema,
            table=table_name,
            error=str(exc),
            exc_info=exc,
        )
        found = False
    _returns_vendor_cache[key] = found
    return found


def clear_caches() -> None:
    """Used in tests to reset ROI cache state."""
    global _returns_vendor_cache
    clear_roi_cache()
    _returns_vendor_cache = _new_vendor_cache()


__all__ = [
    "InvalidROIViewError",
    "get_roi_view_name",
    "get_quoted_roi_view",
    "returns_vendor_column_exists",
    "clear_caches",
    "quote_identifier",
]  # Re-export for routes
