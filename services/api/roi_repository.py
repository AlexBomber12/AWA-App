from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

from sqlalchemy import Column, MetaData, Numeric, String, Table, bindparam, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BindParameter


def _split_schema(roi_view: str) -> tuple[str | None, str]:
    parts = roi_view.split(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, parts[0]


@lru_cache(maxsize=16)
def get_roi_view_table(roi_view: str) -> Table:
    schema, name = _split_schema(roi_view)
    metadata = MetaData()
    return Table(
        name,
        metadata,
        Column("asin", String),
        Column("vendor", String),
        Column("category", String),
        Column("roi", Numeric),
        schema=schema,
    )


async def fetch_scores_for_asins(
    session: AsyncSession,
    asins: Sequence[str],
    roi_view: str,
) -> dict[str, RowMapping]:
    """Return ROI rows keyed by ASIN for the score API."""
    if not asins:
        return {}
    table = get_roi_view_table(roi_view)
    expanding_param: BindParameter[object] = bindparam("asins", expanding=True)
    stmt = select(table.c.asin, table.c.vendor, table.c.category, table.c.roi).where(table.c.asin.in_(expanding_param))
    params = {"asins": tuple(dict.fromkeys(asins))}
    result = await session.execute(stmt, params)
    rows = result.mappings().all()
    return {row["asin"]: row for row in rows}


__all__ = ["fetch_scores_for_asins", "get_roi_view_table"]
