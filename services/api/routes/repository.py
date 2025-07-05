from __future__ import annotations

from typing import Sequence

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import RowMapping

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
      AND (:vendor IS NULL OR vp.vendor_id = :vendor)
      AND (:category IS NULL OR p.category = :category)
    LIMIT 200;
    """
)


async def fetch_roi_rows(
    session: AsyncSession,
    roi_min: float,
    vendor: str | None,
    category: str | None,
) -> list[RowMapping]:
    result = await session.execute(
        ROI_QUERY,
        {"roi_min": roi_min, "vendor": vendor, "category": category},
    )
    return list(result.mappings().all())


BULK_UPDATE = text(
    "UPDATE products SET status='approved' WHERE asin IN :asins"
).bindparams(bindparam("asins", expanding=True))


async def bulk_approve(session: AsyncSession, asins: Sequence[str]) -> int:
    if not asins:
        return 0
    res = await session.execute(BULK_UPDATE, {"asins": tuple(asins)})
    await session.commit()
    return res.rowcount or 0
