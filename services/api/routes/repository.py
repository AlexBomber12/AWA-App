from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.engine import CursorResult, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import TextClause

from services.api.roi_views import get_roi_view_name, quote_identifier


@lru_cache(maxsize=4)
def _roi_query(view_name: str) -> TextClause:
    quoted = quote_identifier(view_name)
    alias = "roi_view"
    return text(
        f"""
        SELECT
          p.asin, p.title, p.category,
          vp.vendor_id,
          vp.cost,
          (p.weight_kg * fr.eur_per_kg)  AS freight,
          (f.fulfil_fee + f.referral_fee + f.storage_fee) AS fees,
          {alias}.roi_pct
        FROM {quoted} AS {alias}
        JOIN products      p  USING (asin)
        JOIN vendor_prices vp ON vp.sku = p.asin
        JOIN freight_rates fr ON fr.lane = 'EU→IT' AND fr.mode = 'sea'
        JOIN fees_raw      f  USING (asin)
        WHERE {alias}.roi_pct >= :roi_min
          AND (:vendor::text IS NULL OR vp.vendor_id = :vendor::text)
          AND (:category::text IS NULL OR p.category = :category::text)
        LIMIT 200;
        """
    )


async def fetch_roi_rows(
    session: AsyncSession, roi_min: float, vendor: int | None, category: str | None
) -> list[RowMapping]:
    view_name = get_roi_view_name()
    stmt = _roi_query(view_name)
    result = await session.execute(stmt, {"roi_min": roi_min, "vendor": vendor, "category": category})
    return list(result.mappings().all())


BULK_UPDATE = text("UPDATE products SET status='approved' WHERE asin IN :asins")


async def bulk_approve(session: AsyncSession, asins: Sequence[str]) -> int:
    if not asins:
        return 0
    res = await session.execute(BULK_UPDATE, {"asins": tuple(asins)})
    await session.commit()
    return cast(CursorResult[Any], res).rowcount or 0
