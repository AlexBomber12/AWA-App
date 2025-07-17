from __future__ import annotations

from typing import Any, Sequence, cast

from sqlalchemy import text
from sqlalchemy.engine import CursorResult, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

ROI_QUERY = text(
    """
    SELECT
      p.asin, p.title, p.category,
      vp.vendor_id,
      vp.cost,
      (p.weight_kg * fr.eur_per_kg)  AS freight,
      (f.fulfil_fee + f.referral_fee + f.storage_fee) AS fees,
      v_roi_full.roi_pct
    FROM v_roi_full
    JOIN products      p  USING (asin)
    JOIN vendor_prices vp ON vp.sku = p.asin
    JOIN freight_rates fr ON fr.lane = 'EU→IT' AND fr.mode = 'sea'
    JOIN fees_raw      f  USING (asin)
    WHERE v_roi_full.roi_pct >= :roi_min
      AND (:vendor::text IS NULL OR vp.vendor_id = :vendor::text)
      AND (:category::text IS NULL OR p.category = :category::text)
    LIMIT 200;
    """
)


async def fetch_roi_rows(
    session: AsyncSession,
    roi_min: float,
    vendor: int | None,
    category: str | None,
) -> list[RowMapping]:
    result = await session.execute(
        ROI_QUERY,
        {"roi_min": roi_min, "vendor": vendor, "category": category},
    )
    return list(result.mappings().all())


BULK_UPDATE = text("UPDATE products SET status='approved' WHERE asin IN :asins")


async def bulk_approve(session: AsyncSession, asins: Sequence[str]) -> int:
    if not asins:
        return 0
    res = await session.execute(BULK_UPDATE, {"asins": tuple(asins)})
    await session.commit()
    return cast(CursorResult[Any], res).rowcount or 0
