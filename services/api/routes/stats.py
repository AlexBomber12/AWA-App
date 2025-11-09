from __future__ import annotations

import os
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import (
    Column,
    Date,
    MetaData,
    Numeric,
    String,
    Table,
    and_,
    bindparam,
    func,
    literal_column,
    select,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.db.async_session import get_async_session
from services.api.roi_repository import get_roi_view_table
from services.api.roi_views import (
    InvalidROIViewError,
    get_roi_view_name,
    returns_vendor_column_exists,
)
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

RETURNS_VIEW_ENV = "RETURNS_STATS_VIEW_NAME"
DEFAULT_RETURNS_VIEW = "returns_raw"
TREND_DATE_CANDIDATES: tuple[str, ...] = ("dt", "date", "snapshot_date", "created_at")


def _sql_mode_enabled() -> bool:
    return os.getenv("STATS_USE_SQL") == "1"


def _split_identifier(identifier: str) -> tuple[str | None, str]:
    parts = identifier.split(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, parts[0]


def _returns_view_name() -> str:
    raw = (os.getenv(RETURNS_VIEW_ENV) or DEFAULT_RETURNS_VIEW).strip()
    return raw or DEFAULT_RETURNS_VIEW


@lru_cache(maxsize=2)
def _returns_table_info() -> tuple[Table, str, str]:
    schema, name = _split_identifier(_returns_view_name())
    metadata = MetaData()
    table = Table(
        name,
        metadata,
        Column("asin", String),
        Column("qty", Numeric),
        Column("refund_amount", Numeric),
        Column("return_date", Date),
        Column("vendor", String),
        schema=schema,
    )
    return table, (schema or "public"), name


def _roi_table_or_400() -> Table:
    try:
        roi_view = get_roi_view_name()
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return get_roi_view_table(roi_view)


@router.get(
    "/kpi",
    response_model=StatsKPIResponse,
    dependencies=[Depends(require_viewer), Depends(limit_viewer)],
)
async def kpi(session: AsyncSession = Depends(get_async_session)) -> StatsKPIResponse:
    if not _sql_mode_enabled():
        return StatsKPIResponse(kpi=StatsKPI(roi_avg=0.0, products=0, vendors=0))

    table = _roi_table_or_400()
    stmt = select(
        func.avg(table.c.roi).label("roi_avg"),
        func.count(func.distinct(table.c.asin)).label("products"),
        func.count(func.distinct(table.c.vendor)).label("vendors"),
    )
    result = await session.execute(stmt)
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

    table = _roi_table_or_400()
    stmt = (
        select(
            table.c.vendor.label("vendor"),
            func.avg(table.c.roi).label("roi_avg"),
            func.count().label("items"),
        )
        .group_by(table.c.vendor)
        .order_by(table.c.vendor.asc())
    )
    result = await session.execute(stmt)
    rows = result.mappings().all()
    items = [
        RoiByVendorItem(
            vendor=row.get("vendor"),
            roi_avg=float(row.get("roi_avg") or 0.0),
            items=int(row.get("items") or 0),
        )
        for row in rows
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

    table, schema, name = _returns_table_info()
    clauses = []
    params: dict[str, object] = {}

    if date_from:
        clauses.append(table.c.return_date >= bindparam("date_from"))
        params["date_from"] = date_from
    if date_to:
        clauses.append(table.c.return_date <= bindparam("date_to"))
        params["date_to"] = date_to
    if asin:
        clauses.append(table.c.asin == bindparam("asin"))
        params["asin"] = asin
    if vendor:
        vendor_available = await returns_vendor_column_exists(session, table_name=name, schema=schema)
        if vendor_available:
            clauses.append(table.c.vendor == bindparam("vendor"))
            params["vendor"] = vendor

    stmt = (
        select(
            table.c.asin.label("asin"),
            func.sum(table.c.qty).label("qty"),
            func.sum(table.c.refund_amount).label("refund_amount"),
        )
        .group_by(table.c.asin)
        .order_by(table.c.asin.asc())
    )
    if clauses:
        stmt = stmt.where(and_(*clauses))

    result = await session.execute(stmt, params or None)
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

    table = _roi_table_or_400()
    for column_name in TREND_DATE_CANDIDATES:
        date_expr = literal_column(column_name)
        month_expr = func.date_trunc("month", date_expr).label("month")
        stmt = (
            select(
                month_expr,
                func.avg(table.c.roi).label("roi_avg"),
                func.count().label("items"),
            )
            .group_by(month_expr)
            .order_by(month_expr.asc())
        )
        try:
            result = await session.execute(stmt)
        except SQLAlchemyError:
            continue
        rows = result.mappings().all()
        if rows:
            points = [
                RoiTrendPoint(
                    month=str(row["month"]),
                    roi_avg=float(row.get("roi_avg") or 0.0),
                    items=int(row.get("items") or 0),
                )
                for row in rows
            ]
            return RoiTrendResponse(points=points)
    return RoiTrendResponse(points=[])
