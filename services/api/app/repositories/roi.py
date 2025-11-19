from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import Any

from sqlalchemy import Numeric, String, bindparam, text
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import TextClause

from awa_common.roi_views import current_roi_view, quote_identifier

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
PENDING_LIMIT = 200
OBSERVE_ONLY_THRESHOLD = 20.0

_FREIGHT_EXPR = "(p.weight_kg * fr.eur_per_kg)"
_FEES_EXPR = "(f.fulfil_fee + f.referral_fee + f.storage_fee)"
_MARGIN_EXPR = f"(COALESCE(vf.roi_pct, 0) / 100.0) * ((COALESCE(vp.cost, 0) + {_FREIGHT_EXPR} + {_FEES_EXPR}))"

ROI_SORT_SQL: dict[str, str] = {
    "roi_pct_desc": "vf.roi_pct DESC NULLS LAST, p.asin ASC",
    "roi_pct_asc": "vf.roi_pct ASC NULLS LAST, p.asin ASC",
    "asin_asc": "p.asin ASC",
    "asin_desc": "p.asin DESC",
    "margin_desc": f"{_MARGIN_EXPR} DESC NULLS LAST, p.asin ASC",
    "margin_asc": f"{_MARGIN_EXPR} ASC NULLS LAST, p.asin ASC",
    "vendor_asc": "vp.vendor_id ASC NULLS LAST, p.asin ASC",
    "vendor_desc": "vp.vendor_id DESC NULLS LAST, p.asin ASC",
}

ROI_DEFAULT_SORT = "roi_pct_desc"


def _page_bounds(page: int | None, page_size: int | None) -> tuple[int, int]:
    safe_page = max(page or 1, 1)
    normalized_size = page_size or DEFAULT_PAGE_SIZE
    safe_size = min(max(normalized_size, 1), MAX_PAGE_SIZE)
    return safe_page, safe_size


def _normalize_sort(sort: str | None) -> str:
    if sort and sort in ROI_SORT_SQL:
        return sort
    return ROI_DEFAULT_SORT


@lru_cache(maxsize=64)
def _roi_listing_sql(
    view_name: str,
    include_vendor: bool,
    include_category: bool,
    include_search: bool,
    include_roi_max: bool,
    sort_key: str,
) -> TextClause:
    quoted = quote_identifier(view_name)
    clauses = ["vf.roi_pct >= :roi_min"]
    if include_roi_max:
        clauses.append("vf.roi_pct <= :roi_max")
    if include_vendor:
        clauses.append("vp.vendor_id = :vendor")
    if include_category:
        clauses.append("LOWER(p.category) = :category")
    if include_search:
        clauses.append("(p.asin ILIKE :search OR p.title ILIKE :search)")
    where_clause = " AND ".join(clauses) if clauses else "TRUE"
    order_by = ROI_SORT_SQL.get(sort_key, ROI_SORT_SQL[ROI_DEFAULT_SORT])
    return text(
        f"""
        SELECT
            p.asin,
            p.title,
            p.category,
            vp.vendor_id,
            vp.cost,
            {_FREIGHT_EXPR} AS freight,
            {_FEES_EXPR} AS fees,
            vf.roi_pct,
            {_MARGIN_EXPR} AS margin_value,
            COUNT(*) OVER() AS total_count
        FROM {quoted} vf
        JOIN products p ON p.asin = vf.asin
        JOIN vendor_prices vp ON vp.sku = p.asin
        JOIN freight_rates fr ON fr.lane = 'EU→IT' AND fr.mode = 'sea'
        JOIN fees_raw f ON f.asin = p.asin
        WHERE {where_clause}
        ORDER BY {order_by}
        LIMIT :limit OFFSET :offset
        """
    )


@lru_cache(maxsize=64)
def _roi_count_sql(
    view_name: str,
    include_vendor: bool,
    include_category: bool,
    include_search: bool,
    include_roi_max: bool,
) -> TextClause:
    quoted = quote_identifier(view_name)
    clauses = ["vf.roi_pct >= :roi_min"]
    if include_roi_max:
        clauses.append("vf.roi_pct <= :roi_max")
    if include_vendor:
        clauses.append("vp.vendor_id = :vendor")
    if include_category:
        clauses.append("LOWER(p.category) = :category")
    if include_search:
        clauses.append("(p.asin ILIKE :search OR p.title ILIKE :search)")
    where_clause = " AND ".join(clauses) if clauses else "TRUE"
    return text(
        f"""
        SELECT COUNT(*) AS total
        FROM {quoted} vf
        JOIN products p ON p.asin = vf.asin
        JOIN vendor_prices vp ON vp.sku = p.asin
        JOIN freight_rates fr ON fr.lane = 'EU→IT' AND fr.mode = 'sea'
        JOIN fees_raw f ON f.asin = p.asin
        WHERE {where_clause}
        """
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
    params.append(bindparam("limit", value=PENDING_LIMIT))
    return text("\n".join(sql)).bindparams(*params)


async def fetch_roi_rows(
    session: AsyncSession,
    roi_min: float,
    vendor: int | None,
    category: str | None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort: str | None = None,
    search: str | None = None,
    roi_max: float | None = None,
) -> tuple[list[RowMapping], int]:
    """Return paginated ROI rows for the public API listing."""
    view_name = current_roi_view()
    safe_sort = _normalize_sort(sort)
    safe_page, safe_size = _page_bounds(page, page_size)
    offset = (safe_page - 1) * safe_size
    include_vendor = vendor is not None
    include_category = bool(category)
    include_search = bool(search)
    include_roi_max = roi_max is not None

    stmt = _roi_listing_sql(
        view_name,
        include_vendor=include_vendor,
        include_category=include_category,
        include_search=include_search,
        include_roi_max=include_roi_max,
        sort_key=safe_sort,
    )
    params: dict[str, object] = {
        "roi_min": roi_min,
        "limit": safe_size,
        "offset": offset,
    }
    if include_vendor:
        params["vendor"] = vendor
    if include_category:
        params["category"] = category
    if include_search and search:
        params["search"] = f"%{search}%"
    if include_roi_max:
        params["roi_max"] = roi_max

    result = await session.execute(stmt, params)
    rows = list(result.mappings().all())
    if rows:
        total = int(rows[0].get("total_count") or 0)
    else:
        total = await _count_roi_rows(
            session, view_name, include_vendor, include_category, include_search, include_roi_max, params
        )
    return rows, total


async def _count_roi_rows(
    session: AsyncSession,
    view_name: str,
    include_vendor: bool,
    include_category: bool,
    include_search: bool,
    include_roi_max: bool,
    params: dict[str, object],
) -> int:
    stmt = _roi_count_sql(
        view_name,
        include_vendor=include_vendor,
        include_category=include_category,
        include_search=include_search,
        include_roi_max=include_roi_max,
    )
    count_params = {key: value for key, value in params.items() if key not in {"limit", "offset"}}
    result = await session.execute(stmt, count_params)
    scalar_fn = getattr(result, "scalar_one_or_none", None)
    if callable(scalar_fn):
        total = scalar_fn()
    else:
        total = result.scalar()
    return int(total or 0)


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
    params: dict[str, object] = {"roi_min": roi_min, "limit": PENDING_LIMIT}
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
