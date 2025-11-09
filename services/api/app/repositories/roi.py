from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import Any

from sqlalchemy import Numeric, String, bindparam, text
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import TextClause

from awa_common.roi_views import current_roi_view, quote_identifier

DEFAULT_LIMIT = 200


@lru_cache(maxsize=16)
def _roi_listing_sql(view_name: str) -> TextClause:
    quoted = quote_identifier(view_name)
    return text(
        f"""
        SELECT p.asin, p.title, p.category,
               vp.vendor_id, vp.cost,
               (p.weight_kg * fr.eur_per_kg)  AS freight,
               (f.fulfil_fee + f.referral_fee + f.storage_fee) AS fees,
               vf.roi_pct
        FROM {quoted} vf
        JOIN products      p  USING (asin)
        JOIN vendor_prices vp ON vp.sku = p.asin
        JOIN freight_rates fr ON fr.lane = 'EU→IT' AND fr.mode = 'sea'
        JOIN fees_raw      f  USING (asin)
        WHERE vf.roi_pct >= :roi_min
          AND (:vendor IS NULL OR vp.vendor_id = :vendor)
          AND (:category IS NULL OR p.category = :category)
        LIMIT :limit
        """
    ).bindparams(
        bindparam("roi_min", type_=Numeric),
        bindparam("vendor", type_=String),
        bindparam("category", type_=String),
        bindparam("limit", value=DEFAULT_LIMIT),
    )


@lru_cache(maxsize=8)
def _pending_sql(view_name: str, include_vendor: bool, include_category: bool) -> TextClause:
    quoted = quote_identifier(view_name)
    sql = [
        f"""
        SELECT p.asin, p.title, p.category,
               vp.vendor_id, vp.cost,
               (p.weight_kg * fr.eur_per_kg) AS freight,
               (f.fulfil_fee + f.referral_fee + f.storage_fee) AS fees,
               vf.roi_pct
        FROM {quoted} vf
        JOIN products p   ON p.asin = vf.asin
        JOIN vendor_prices vp ON vp.sku = p.asin
        JOIN freight_rates fr ON fr.lane = 'EU→IT' AND fr.mode = 'sea'
        JOIN fees_raw f  ON f.asin = p.asin
        WHERE vf.roi_pct >= :roi_min
          AND COALESCE(p.status, 'pending') = 'pending'
        """
    ]
    params: list[Any] = [bindparam("roi_min", type_=Numeric)]
    if include_vendor:
        sql.append("  AND vp.vendor_id = :vendor")
        params.append(bindparam("vendor", type_=String))
    if include_category:
        sql.append("  AND p.category = :category")
        params.append(bindparam("category", type_=String))
    sql.append("  LIMIT :limit")
    params.append(bindparam("limit", value=DEFAULT_LIMIT))
    return text("\n".join(sql)).bindparams(*params)


async def fetch_roi_rows(
    session: AsyncSession,
    roi_min: float,
    vendor: int | None,
    category: str | None,
) -> list[RowMapping]:
    """Return ROI rows for the public API listing."""
    stmt = _roi_listing_sql(current_roi_view())
    result = await session.execute(
        stmt,
        {"roi_min": roi_min, "vendor": vendor, "category": category, "limit": DEFAULT_LIMIT},
    )
    return list(result.mappings().all())


async def fetch_pending_rows(
    session: AsyncSession,
    roi_min: float,
    vendor: int | None,
    category: str | None,
) -> list[RowMapping]:
    """Return pending ROI rows for the ROI review UI."""
    stmt = _pending_sql(
        current_roi_view(),
        include_vendor=vendor is not None,
        include_category=category is not None,
    )
    params: dict[str, object] = {"roi_min": roi_min, "limit": DEFAULT_LIMIT}
    if vendor is not None:
        params["vendor"] = str(vendor)
    if category is not None:
        params["category"] = category
    result = await session.execute(stmt, params)
    return list(result.mappings().all())


APPROVE_SQL = text(
    """
        UPDATE products
           SET status = 'approved'
         WHERE asin IN :asins
           AND COALESCE(status, 'pending') = 'pending'
         RETURNING asin
        """
).bindparams(bindparam("asins", expanding=True))


async def bulk_approve(
    session: AsyncSession,
    asins: Sequence[str],
    approved_by: str | None = None,
) -> list[str]:
    """Mark the provided ASINs as approved atomically, returning the updated ASINs."""
    if not asins:
        return []
    deduped = tuple(dict.fromkeys(asins))
    # The schema does not yet capture approved_by; keep the argument for future parity.
    _ = approved_by
    async with session.begin():
        result = await session.execute(APPROVE_SQL, {"asins": deduped})
        approved_raw = result.scalars().all()
    approved = [str(asin) for asin in approved_raw]
    return approved


__all__ = ["bulk_approve", "fetch_pending_rows", "fetch_roi_rows"]
