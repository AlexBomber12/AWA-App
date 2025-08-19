from __future__ import annotations

import os
from typing import Sequence

from sqlalchemy import ARRAY, Numeric, String, bindparam, text
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

ROI_VIEW_NAME = os.getenv("ROI_VIEW_NAME", "v_roi_full")


def _roi_view_name() -> str:
    # Used for SELECTs; production keeps default "v_roi_full"
    return ROI_VIEW_NAME


ROI_SQL = text(
    f"""
    SELECT p.asin, p.title, p.category,
           vp.vendor_id, vp.cost,
           (p.weight_kg * fr.eur_per_kg)  AS freight,
           (f.fulfil_fee + f.referral_fee + f.storage_fee) AS fees,
           vf.roi_pct
    FROM {_roi_view_name()} vf
    JOIN products      p  USING (asin)
    JOIN vendor_prices vp ON vp.sku = p.asin
    JOIN freight_rates fr ON fr.lane = 'EU→IT' AND fr.mode = 'sea'
    JOIN fees_raw      f  USING (asin)
    WHERE vf.roi_pct >= :roi_min
      AND (:vendor IS NULL OR vp.vendor_id = :vendor)
      AND (:category IS NULL OR p.category = :category)
    LIMIT 200
    """
).bindparams(
    bindparam("vendor", type_=String),
    bindparam("category", type_=String),
    bindparam("roi_min", type_=Numeric),
)


async def fetch_roi_rows(
    session: AsyncSession, roi_min: float, vendor: int | None, category: str | None
) -> list[RowMapping]:
    result = await session.execute(
        ROI_SQL, {"roi_min": roi_min, "vendor": vendor, "category": category}
    )
    return list(result.mappings().all())


APPROVE_SQL = text(
    """
    UPDATE products
       SET status = 'approved'
     WHERE asin = ANY(:asins)
       AND COALESCE(status,'pending') = 'pending'
     RETURNING asin
    """
).bindparams(bindparam("asins", ARRAY(String)))


async def bulk_approve(session: AsyncSession, asins: Sequence[str]) -> int:
    if not asins:
        return 0
    res = await session.execute(APPROVE_SQL, {"asins": asins})
    rows = res.scalars().all()
    await session.commit()
    return len(rows)
