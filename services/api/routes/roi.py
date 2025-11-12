from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.db.async_session import get_async_session
from awa_common.roi_views import InvalidROIViewError
from services.api.app.repositories import roi as roi_repository
from services.api.schemas import RoiApprovalResponse, RoiRow
from services.api.security import limit_ops, limit_viewer, require_ops, require_viewer

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
    session: AsyncSession = Depends(get_async_session),
    _: object = Depends(require_viewer),
    __: None = Depends(limit_viewer),
) -> list[RoiRow]:
    try:
        rows = await roi_repository.fetch_roi_rows(session, roi_min, vendor, category)
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return [_serialize_roi_row(dict(row)) for row in rows]


@router.get("/roi-review")
async def roi_review(
    request: Request,
    roi_min: int = 0,
    vendor: int | None = None,
    category: str | None = None,
    session: AsyncSession = Depends(get_async_session),
    _: object = Depends(require_ops),
    __: None = Depends(limit_ops),
):
    try:
        rows = await roi_repository.fetch_pending_rows(session, roi_min, vendor, category)
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    resolved_rows = [dict(row) if isinstance(row, Mapping) else dict(row._mapping) for row in rows]
    context = {
        "request": request,
        "rows": resolved_rows,
        "roi_min": roi_min,
        "vendor": vendor,
        "category": category,
    }
    return templates.TemplateResponse("roi_review.html", context)


async def _extract_asins(request: Request) -> list[str]:
    if request.headers.get("content-type", "").startswith("application/json"):
        data = await request.json()
        return data.get("asins", [])
    form = await request.form()
    values = form.getlist("asins")
    return [str(value) for value in values]


def _resolve_approver(request: Request) -> str | None:
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    for attr in ("email", "sub"):
        value = getattr(user, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


@router.post("/roi-review/approve", response_model=RoiApprovalResponse)
async def approve(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    _: object = Depends(require_ops),
    __: None = Depends(limit_ops),
) -> RoiApprovalResponse:
    asins = await _extract_asins(request)
    if not asins:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No ASINs provided")
    approved = await roi_repository.bulk_approve(session, asins, approved_by=_resolve_approver(request))
    if not approved:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending SKUs matched selection")
    return RoiApprovalResponse(updated=len(approved), approved_ids=approved)
