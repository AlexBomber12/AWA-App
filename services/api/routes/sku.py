from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from functools import cache
from typing import Any, TypedDict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Integer, bindparam, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import TextClause

from .. import roi_repository
from ..db import get_session
from ..roi_views import InvalidROIViewError, get_roi_view_name, quote_identifier
from ..security import limit_ops, limit_viewer, require_ops, require_viewer

router = APIRouter(tags=["sku"])


def _roi_view_name() -> str:
    return get_roi_view_name()


class ChartPoint(TypedDict):
    date: str
    price: float


@cache
def _sku_card_sql(view_name: str) -> TextClause:
    quoted_view = quote_identifier(view_name)
    return sa_text(
        f"""
        SELECT p.title, r.roi_pct, r.fees
          FROM products AS p
          JOIN {quoted_view} AS r ON r.asin = p.asin
         WHERE p.asin = :asin
         LIMIT 1
        """
    )


SKU_CHART_SQL = sa_text(
    """
        SELECT captured_at AS date, price
          FROM buybox
         WHERE asin = :asin
         ORDER BY captured_at DESC
         LIMIT :limit
        """
).bindparams(bindparam("limit", type_=Integer))


def _to_iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None:
        return ""
    return str(value)


def _serialize_chart(rows: Iterable[Mapping[str, Any]]) -> list[ChartPoint]:
    items: list[ChartPoint] = []
    for row in reversed(list(rows)):
        date_value = row.get("date")
        price_value = row.get("price")
        try:
            price = float(price_value) if price_value is not None else 0.0
        except (TypeError, ValueError):
            price = 0.0
        items.append({"date": _to_iso(date_value), "price": price})
    return items


@router.get("/sku/{asin}")
async def get_sku(
    asin: str,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(require_viewer),
    __: None = Depends(limit_viewer),
) -> dict[str, Any]:
    """Return title, ROI, fees, and recent price history for a SKU."""
    try:
        stmt = _sku_card_sql(_roi_view_name())
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    result = await session.execute(stmt, {"asin": asin})
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    chart_result = await session.execute(SKU_CHART_SQL, {"asin": asin, "limit": 180})
    chart_rows = [dict(row) for row in chart_result.mappings().all()]
    return {
        "title": row.get("title") or "",
        "roi": float(row.get("roi_pct") or 0.0),
        "fees": float(row.get("fees") or 0.0),
        "chartData": _serialize_chart(chart_rows),
    }


@router.post("/sku/{asin}/approve")
async def approve_sku(
    asin: str,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(require_ops),
    __: None = Depends(limit_ops),
) -> dict[str, Any]:
    """Mark the SKU as approved if pending, returning the number of changes."""
    changed = await roi_repository.bulk_approve(session, [asin])
    return {"approved": True, "changed": int(changed)}


__all__ = ["router", "get_sku", "approve_sku"]
