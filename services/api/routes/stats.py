from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.db.async_session import get_async_session
from awa_common.roi_views import InvalidROIViewError, current_roi_view, quote_identifier
from services.api.schemas import (
    ReturnsStatsItem,
    ReturnsStatsResponse,
    RoiByVendorItem,
    RoiByVendorResponse,
    RoiTrendPoint,
    RoiTrendResponse,
    StatsKPI,
    StatsKPIResponse,
)
from services.api.security import limit_viewer, require_viewer

router = APIRouter(prefix="/stats", tags=["stats"])

_RETURNS_VENDOR_COLUMN: bool | None = None


def _sql_mode_enabled() -> bool:
    return os.getenv("STATS_USE_SQL") == "1"


async def _returns_vendor_available(session: AsyncSession) -> bool:
    global _RETURNS_VENDOR_COLUMN
    if _RETURNS_VENDOR_COLUMN is not None:
        return _RETURNS_VENDOR_COLUMN
    try:
        result = await session.execute(
            text(
                """
                SELECT 1
                  FROM information_schema.columns
                 WHERE table_schema = 'public'
                   AND table_name = 'returns_raw'
                   AND column_name = 'vendor'
                 LIMIT 1
                """
            )
        )
        _RETURNS_VENDOR_COLUMN = bool(result.scalar())
    except Exception:
        _RETURNS_VENDOR_COLUMN = False
    return _RETURNS_VENDOR_COLUMN


def _quoted_roi_view() -> str:
    return quote_identifier(current_roi_view())


@router.get(
    "/kpi",
    response_model=StatsKPIResponse,
    dependencies=[Depends(require_viewer), Depends(limit_viewer)],
)
async def kpi(session: AsyncSession = Depends(get_async_session)) -> StatsKPIResponse:
    if not _sql_mode_enabled():
        return StatsKPIResponse(kpi=StatsKPI(roi_avg=0.0, products=0, vendors=0))
    try:
        view = _quoted_roi_view()
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    result = await session.execute(
        text(
            "SELECT AVG(roi) AS roi_avg, "
            "COUNT(DISTINCT asin) AS products, "
            "COUNT(DISTINCT vendor) AS vendors "
            f"FROM {view}"
        )
    )
    row = (result.mappings().first()) or {}
    metrics = StatsKPI(
        roi_avg=float(row.get("roi_avg") or 0.0),
        products=int(row.get("products") or 0),
        vendors=int(row.get("vendors") or 0),
    )
    return StatsKPIResponse(kpi=metrics)


@router.get(
    "/roi_by_vendor",
    response_model=RoiByVendorResponse,
    dependencies=[Depends(require_viewer), Depends(limit_viewer)],
)
async def roi_by_vendor(session: AsyncSession = Depends(get_async_session)) -> RoiByVendorResponse:
    if not _sql_mode_enabled():
        return RoiByVendorResponse(items=[], total_vendors=0)
    try:
        view = _quoted_roi_view()
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    result = await session.execute(
        text(
            f"""
            SELECT vendor, AVG(roi) AS roi_avg, COUNT(*) AS items
              FROM {view}
          GROUP BY vendor
          ORDER BY vendor
            """
        )
    )
    rows = result.mappings().all()
    items = [
        RoiByVendorItem(
            vendor=r.get("vendor"),
            roi_avg=float(r.get("roi_avg") or 0.0),
            items=int(r.get("items") or 0),
        )
        for r in rows
    ]
    return RoiByVendorResponse(items=items, total_vendors=len(items))


@router.get(
    "/returns",
    response_model=ReturnsStatsResponse,
    dependencies=[Depends(require_viewer), Depends(limit_viewer)],
)
async def returns_stats(
    date_from: str | None = None,
    date_to: str | None = None,
    asin: str | None = None,
    vendor: str | None = None,
    session: AsyncSession = Depends(get_async_session),
) -> ReturnsStatsResponse:
    if not _sql_mode_enabled():
        return ReturnsStatsResponse(items=[], total_returns=0)

    clauses: list[str] = []
    params: dict[str, str] = {}

    if date_from:
        clauses.append("return_date >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("return_date <= :date_to")
        params["date_to"] = date_to
    if asin:
        clauses.append("asin = :asin")
        params["asin"] = asin
    if vendor and await _returns_vendor_available(session):
        clauses.append("vendor = :vendor")
        params["vendor"] = vendor

    query_parts = [
        "SELECT asin, SUM(qty) AS qty, SUM(refund_amount) AS refund_amount",
        "FROM returns_raw",
    ]
    if clauses:
        query_parts.append("WHERE " + " AND ".join(clauses))
    query_parts.append("GROUP BY asin ORDER BY asin")
    sql = " ".join(query_parts)

    result = await session.execute(text(sql), params)
    rows = result.mappings().all()
    items = [
        ReturnsStatsItem(
            asin=row["asin"],
            qty=int(row.get("qty") or 0),
            refund_amount=float(row.get("refund_amount") or 0.0),
        )
        for row in rows
    ]
    return ReturnsStatsResponse(items=items, total_returns=len(items))


@router.get(
    "/roi_trend",
    response_model=RoiTrendResponse,
    dependencies=[Depends(require_viewer), Depends(limit_viewer)],
)
async def roi_trend(session: AsyncSession = Depends(get_async_session)) -> RoiTrendResponse:
    if not _sql_mode_enabled():
        return RoiTrendResponse(points=[])
    try:
        view = _quoted_roi_view()
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    for date_col in ("dt", "date", "snapshot_date", "created_at"):
        try:
            result = await session.execute(
                text(
                    f"SELECT date_trunc('month', {date_col})::date AS month, "
                    "AVG(roi) AS roi_avg, COUNT(*) AS items "
                    f"FROM {view} GROUP BY 1 ORDER BY 1"
                )
            )
        except Exception:
            continue
        rows = result.mappings().all()
        if rows:
            points = [
                RoiTrendPoint(
                    month=str(r["month"]),
                    roi_avg=float(r.get("roi_avg") or 0.0),
                    items=int(r.get("items") or 0),
                )
                for r in rows
            ]
            return RoiTrendResponse(points=points)
    return RoiTrendResponse(points=[])
