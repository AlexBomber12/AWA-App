from __future__ import annotations

import datetime as dt
import os
import time
from collections.abc import Mapping
from functools import lru_cache
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
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

from awa_common.cache import (
    build_cache_key,
    get_json,
    normalize_namespace,
    set_json,
    set_returns_metadata,
)
from awa_common.db.async_session import get_async_session
from awa_common.metrics import (
    record_stats_cache_hit,
    record_stats_cache_miss,
    record_stats_query_duration,
)
from awa_common.settings import settings
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
logger = structlog.get_logger(__name__)

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


def _stats_cache_enabled() -> bool:
    try:
        return bool(getattr(settings, "STATS_ENABLE_CACHE", True))
    except Exception:
        return True


def _stats_cache_client(request: Request | None):
    if request is None:
        return None
    app = getattr(request, "app", None)
    state = getattr(app, "state", None) if app is not None else None
    return getattr(state, "stats_cache", None)


def _stats_namespace(request: Request | None) -> str:
    state_ns = None
    if request is not None:
        app = getattr(request, "app", None)
        state = getattr(app, "state", None) if app is not None else None
        state_ns = getattr(state, "stats_cache_namespace", None)
    try:
        configured = getattr(settings, "STATS_CACHE_NAMESPACE", "stats:")
    except Exception:
        configured = "stats:"
    return normalize_namespace(state_ns or configured)


def _cache_ttl() -> int:
    try:
        ttl = int(getattr(settings, "STATS_CACHE_TTL_S", 0))
    except Exception:
        ttl = 0
    if ttl <= 0:
        return 0
    return max(60, min(ttl, 1800))


async def _maybe_get_cached_response(
    request: Request | None,
    *,
    endpoint: str,
    params: Mapping[str, Any] | None = None,
) -> tuple[Any | None, str | None, Any]:
    client = _stats_cache_client(request) if _stats_cache_enabled() else None
    if client is None:
        return None, None, None
    cache_key = build_cache_key(_stats_namespace(request), endpoint, params)
    payload = await get_json(client, cache_key)
    if payload is not None:
        record_stats_cache_hit(endpoint)
        logger.debug("stats_cache_hit", endpoint=endpoint, cache_key=cache_key)
        return payload, cache_key, client
    record_stats_cache_miss(endpoint)
    logger.debug("stats_cache_miss", endpoint=endpoint, cache_key=cache_key)
    return None, cache_key, client


async def _store_cached_response(
    cache_client,
    *,
    cache_key: str | None,
    endpoint: str,
    payload: Any,
) -> None:
    if cache_client is None or not cache_key:
        return
    ttl = _cache_ttl()
    if ttl <= 0:
        return
    stored = await set_json(cache_client, cache_key, payload, ttl)
    if not stored:
        logger.debug("stats_cache_store_failed", endpoint=endpoint, cache_key=cache_key)


async def _observe_query(endpoint: str, operation) -> Any:
    start = time.perf_counter()
    try:
        return await operation
    finally:
        duration = time.perf_counter() - start
        record_stats_query_duration(endpoint, duration)


def _parse_date(value: str | None, field: str) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - FastAPI validates in production, tests guard as well
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid {field}") from exc


def _enforce_date_limits(start: dt.date | None, end: dt.date | None) -> tuple[dt.date | None, dt.date | None]:
    if start is None or end is None:
        return start, end
    if end < start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_to must be greater than or equal to date_from",
        )
    max_days = max(int(getattr(settings, "STATS_MAX_DAYS", 365) or 0), 1)
    span = (end - start).days + 1
    if span <= max_days:
        return start, end
    if bool(getattr(settings, "REQUIRE_CLAMP", False)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Requested window exceeds {max_days} days",
        )
    clamped_start = end - dt.timedelta(days=max_days - 1)
    logger.debug(
        "stats_returns_clamped_window",
        original_start=start.isoformat(),
        original_end=end.isoformat(),
        clamped_start=clamped_start.isoformat(),
        clamped_end=end.isoformat(),
        max_days=max_days,
    )
    return clamped_start, end


@router.get(
    "/kpi",
    response_model=StatsKPIResponse,
    dependencies=[Depends(require_viewer), Depends(limit_viewer)],
)
async def kpi(
    session: AsyncSession = Depends(get_async_session),
    request: Request = None,
) -> StatsKPIResponse:
    if not _sql_mode_enabled():
        return StatsKPIResponse(kpi=StatsKPI(roi_avg=0.0, products=0, vendors=0))

    cached, cache_key, cache_client = await _maybe_get_cached_response(request, endpoint="kpi")
    if isinstance(cached, dict):
        return StatsKPIResponse.model_validate(cached)

    table = _roi_table_or_400()
    stmt = select(
        func.avg(table.c.roi).label("roi_avg"),
        func.count(func.distinct(table.c.asin)).label("products"),
        func.count(func.distinct(table.c.vendor)).label("vendors"),
    )
    result = await _observe_query("kpi", session.execute(stmt))
    row = (result.mappings().first()) or {}
    metrics = StatsKPI(
        roi_avg=float(row.get("roi_avg") or 0.0),
        products=int(row.get("products") or 0),
        vendors=int(row.get("vendors") or 0),
    )
    response = StatsKPIResponse(kpi=metrics)
    await _store_cached_response(cache_client, cache_key=cache_key, endpoint="kpi", payload=response.model_dump())
    return response


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
    group_by: str = "asin",
    session: AsyncSession = Depends(get_async_session),
    request: Request = None,
) -> ReturnsStatsResponse:
    if not _sql_mode_enabled():
        return ReturnsStatsResponse(items=[], total_returns=0)

    parsed_from = _parse_date(date_from, "date_from")
    parsed_to = _parse_date(date_to, "date_to")
    bounded_from, bounded_to = _enforce_date_limits(parsed_from, parsed_to)
    normalized_group = (group_by or "asin").strip().lower() or "asin"
    if normalized_group != "asin":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only group_by=asin is supported at this time.",
        )
    cache_params = {
        "date_from": bounded_from.isoformat() if bounded_from else "",
        "date_to": bounded_to.isoformat() if bounded_to else "",
        "asin": asin or "",
        "vendor": vendor or "",
        "group_by": normalized_group,
    }
    cached, cache_key, cache_client = await _maybe_get_cached_response(
        request,
        endpoint="returns",
        params=cache_params,
    )
    if isinstance(cached, dict):
        return ReturnsStatsResponse.model_validate(cached)

    table, schema, name = _returns_table_info()
    clauses = []
    params: dict[str, object] = {}

    if bounded_from:
        clauses.append(table.c.return_date >= bindparam("date_from"))
        params["date_from"] = bounded_from
    if bounded_to:
        clauses.append(table.c.return_date <= bindparam("date_to"))
        params["date_to"] = bounded_to
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

    result = await _observe_query("returns", session.execute(stmt, params or None))
    rows = result.mappings().all()
    items = [
        ReturnsStatsItem(
            asin=row["asin"],
            qty=int(row.get("qty") or 0),
            refund_amount=float(row.get("refund_amount") or 0.0),
        )
        for row in rows
    ]
    response = ReturnsStatsResponse(items=items, total_returns=len(items))
    payload = response.model_dump()
    await _store_cached_response(cache_client, cache_key=cache_key, endpoint="returns", payload=payload)
    ttl = _cache_ttl()
    if cache_client is not None and cache_key and ttl > 0:
        await set_returns_metadata(cache_client, cache_key, date_from=bounded_from, date_to=bounded_to, ttl_s=ttl)
    return response


@router.get(
    "/roi_trend",
    response_model=RoiTrendResponse,
    dependencies=[Depends(require_viewer), Depends(limit_viewer)],
)
async def roi_trend(
    session: AsyncSession = Depends(get_async_session),
    request: Request = None,
) -> RoiTrendResponse:
    if not _sql_mode_enabled():
        return RoiTrendResponse(points=[])

    cached, cache_key, cache_client = await _maybe_get_cached_response(request, endpoint="roi_trend")
    if isinstance(cached, dict):
        return RoiTrendResponse.model_validate(cached)

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
            result = await _observe_query("roi_trend", session.execute(stmt))
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
            response = RoiTrendResponse(points=points)
            await _store_cached_response(
                cache_client, cache_key=cache_key, endpoint="roi_trend", payload=response.model_dump()
            )
            return response
    empty = RoiTrendResponse(points=[])
    await _store_cached_response(cache_client, cache_key=cache_key, endpoint="roi_trend", payload=empty.model_dump())
    return empty
