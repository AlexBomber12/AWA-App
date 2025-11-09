from __future__ import annotations

import os
from collections.abc import Callable
from typing import Final, cast

from cachetools import TTLCache
from sqlalchemy import Column, MetaData, String, Table, select
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.roi_views import InvalidROIViewError, current_roi_view, quote_identifier


def _resolve_current_roi_view() -> str:
    resolver: Callable[[], str] = current_roi_view
    return resolver()


def _quote_roi_view(identifier: str) -> str:
    formatter: Callable[[str], str] = quote_identifier
    return formatter(identifier)


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
    raw = os.getenv(ROI_CACHE_TTL_ENV)
    try:
        value = float(raw) if raw else DEFAULT_CACHE_TTL_SECONDS
    except (TypeError, ValueError):
        value = DEFAULT_CACHE_TTL_SECONDS
    return value if value > 0 else DEFAULT_CACHE_TTL_SECONDS


def _new_cache() -> TTLCache[str, object]:
    return TTLCache(maxsize=_CACHE_SIZE, ttl=_ttl_seconds())


_roi_cache = cast(TTLCache[str, str], _new_cache())
_returns_vendor_cache = cast(TTLCache[str, bool], _new_cache())

_ROI_VIEW_KEY = "roi_view"


def get_roi_view_name() -> str:
    """Return the configured ROI view name, cached for a short TTL."""
    cached = _roi_cache.get(_ROI_VIEW_KEY)
    if isinstance(cached, str):
        return cached
    resolved = _resolve_current_roi_view()
    _roi_cache[_ROI_VIEW_KEY] = resolved
    return resolved


def get_quoted_roi_view() -> str:
    """Return the cached ROI view name quoted for SQL usage."""
    return _quote_roi_view(get_roi_view_name())


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
    except Exception:
        found = False
    _returns_vendor_cache[key] = found
    return found


def clear_caches() -> None:
    """Used in tests to reset ROI cache state."""
    global _roi_cache, _returns_vendor_cache
    _roi_cache = cast(TTLCache[str, str], _new_cache())
    _returns_vendor_cache = cast(TTLCache[str, bool], _new_cache())


__all__ = [
    "InvalidROIViewError",
    "get_roi_view_name",
    "get_quoted_roi_view",
    "returns_vendor_column_exists",
    "clear_caches",
    "quote_identifier",
]  # Re-export for routes
