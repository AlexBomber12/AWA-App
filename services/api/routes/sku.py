from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping, TypedDict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Integer, bindparam
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from .. import roi_repository
from ..db import get_session

router = APIRouter(tags=["sku"])


def _roi_view_name() -> str:
    getter = getattr(roi_repository, "_roi_view_name", None)
    if callable(getter):
        value = getter()
        if isinstance(value, str):
            return value
    return "v_roi_full"


class ChartPoint(TypedDict):
    date: str
    price: float


SKU_CARD_SQL = sa_text(
    f"""
    SELECT p.title, r.roi_pct, r.fees
      FROM products AS p
      JOIN {_roi_view_name()} AS r ON r.asin = p.asin
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
    asin: str, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    """Return title, ROI, fees, and recent price history for a SKU."""
    result = await session.execute(SKU_CARD_SQL, {"asin": asin})
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
    asin: str, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    """Mark the SKU as approved if pending, returning the number of changes."""
    changed = await roi_repository.bulk_approve(session, [asin])
    return {"approved": True, "changed": int(changed)}


__all__ = ["router", "get_sku", "approve_sku"]
