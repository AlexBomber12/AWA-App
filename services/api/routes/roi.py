from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import String, bindparam, create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Numeric

from awa_common.dsn import build_dsn

from .. import roi_repository
from ..db import get_session
from ..roi_views import InvalidROIViewError, get_roi_view_name, quote_identifier
from ..schemas import RoiApprovalResponse, RoiRow
from ..security import limit_ops, limit_viewer, require_ops, require_viewer

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _serialize_roi_row(row: Mapping[str, Any]) -> RoiRow:
    return RoiRow(
        asin=str(row.get("asin") or ""),
        title=row.get("title"),
        category=row.get("category"),
        vendor_id=_to_int(row.get("vendor_id")),
        cost=_to_float(row.get("cost")),
        freight=_to_float(row.get("freight")),
        fees=_to_float(row.get("fees")),
        roi_pct=_to_float(row.get("roi_pct")),
    )


@router.get("/roi", response_model=list[RoiRow])
async def roi(
    roi_min: float = 0,
    vendor: int | None = None,
    category: str | None = None,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(require_viewer),
    __: None = Depends(limit_viewer),
) -> list[RoiRow]:
    try:
        rows = await roi_repository.fetch_roi_rows(session, roi_min, vendor, category)
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return [_serialize_roi_row(dict(row)) for row in rows]


def build_pending_sql(include_vendor: bool, include_category: bool):
    view_identifier = quote_identifier(get_roi_view_name())
    base = """
        SELECT p.asin, p.title, p.category,
               vp.vendor_id, vp.cost,
               (p.weight_kg * fr.eur_per_kg) AS freight,
               (f.fulfil_fee + f.referral_fee + f.storage_fee) AS fees,
               vf.roi_pct
        FROM {view} vf
        JOIN products p   ON p.asin = vf.asin
        JOIN vendor_prices vp ON vp.sku = p.asin
        JOIN freight_rates fr ON fr.lane = 'EU→IT' AND fr.mode = 'sea'
        JOIN fees_raw f  ON f.asin = p.asin
        WHERE vf.roi_pct >= :roi_min
          AND COALESCE(p.status, 'pending') = 'pending'
    """
    base = base.format(view=view_identifier)
    params = [bindparam("roi_min", type_=Numeric)]
    if include_vendor:
        base += " AND vp.vendor_id = :vendor"
        params.append(bindparam("vendor", type_=String))
    if include_category:
        base += " AND p.category   = :category"
        params.append(bindparam("category", type_=String))
    base += " LIMIT 200"
    return text(base).bindparams(*params)


@router.get("/roi-review")
def roi_review(
    request: Request,
    roi_min: int = 0,
    vendor: int | None = None,
    category: str | None = None,
    _: object = Depends(require_ops),
    __: None = Depends(limit_ops),
):
    url = build_dsn(sync=True)
    engine = create_engine(url)
    try:
        stmt = build_pending_sql(vendor is not None, category is not None)
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    params = {"roi_min": roi_min}
    if vendor is not None:
        params["vendor"] = vendor
    if category is not None:
        params["category"] = category
    with engine.connect() as conn:
        res = conn.execute(stmt, params)
        items = [dict(row._mapping) for row in res.fetchall()]
    engine.dispose()
    context = {
        "request": request,
        "items": items,
        "rows": items,
        "roi_min": roi_min,
        "vendor": vendor,
        "category": category,
    }
    return templates.TemplateResponse("roi_review.html", context)


APPROVE_SQL = text(
    """
    UPDATE products
       SET status = 'approved'
     WHERE asin = ANY(:asins)
       AND COALESCE(status,'pending') = 'pending'
     RETURNING asin
    """
).bindparams(bindparam("asins", expanding=True))


async def _extract_asins(request: Request) -> list[str]:
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
        return data.get("asins", [])
    form = await request.form()
    values = form.getlist("asins")
    return [str(value) for value in values]


@router.post("/roi-review/approve", response_model=RoiApprovalResponse)
async def approve(
    request: Request,
    _: object = Depends(require_ops),
    __: None = Depends(limit_ops),
) -> RoiApprovalResponse:
    asins = await _extract_asins(request)
    if not asins:
        return RoiApprovalResponse(updated=0)
    url = build_dsn(sync=True)
    engine = create_engine(url)
    with engine.begin() as conn:
        rows = conn.execute(APPROVE_SQL, {"asins": asins}).scalars().all()
        count = len(rows)
    engine.dispose()
    return RoiApprovalResponse(updated=count)
