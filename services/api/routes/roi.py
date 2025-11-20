from __future__ import annotations

from collections.abc import Mapping
from math import ceil
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.db.async_session import get_async_session
from awa_common.roi_views import InvalidROIViewError
from services.api.app.repositories import roi as roi_repository
from services.api.schemas import PaginationMeta, RoiApprovalResponse, RoiListResponse, RoiRow
from services.api.security import limit_ops, limit_viewer, require_ops, require_viewer

router = APIRouter()
template_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))

RoiSort = Literal[
    "roi_pct_desc",
    "roi_pct_asc",
    "asin_asc",
    "asin_desc",
    "margin_desc",
    "margin_asc",
    "vendor_asc",
    "vendor_desc",
]
ROI_DEFAULT_SORT: RoiSort = "roi_pct_desc"
ROI_DEFAULT_PAGE_SIZE = getattr(roi_repository, "DEFAULT_PAGE_SIZE", 50)
ROI_MAX_PAGE_SIZE = getattr(roi_repository, "MAX_PAGE_SIZE", 200)
OBSERVE_ONLY_THRESHOLD = getattr(roi_repository, "OBSERVE_ONLY_THRESHOLD", 20.0)


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


def _normalize_text(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return None
    candidate = value.strip()
    return candidate or None


def _normalize_positive_int(value: int | None, fallback: int, max_value: int | None = None) -> int:
    if isinstance(value, int) and value > 0:
        result = value
    else:
        result = fallback
    if max_value is not None:
        return min(result, max_value)
    return result


@router.get("/roi", response_model=RoiListResponse)
async def roi(
    roi_min: float = 0,
    vendor: int | None = None,
    category: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(ROI_DEFAULT_PAGE_SIZE, ge=1, le=ROI_MAX_PAGE_SIZE),
    sort: RoiSort = Query(ROI_DEFAULT_SORT),
    search: str | None = Query(None, max_length=64),
    observe_only: bool = Query(False),
    roi_max: float | None = Query(None),
    session: AsyncSession = Depends(get_async_session),
    _: object = Depends(require_viewer),
    __: None = Depends(limit_viewer),
) -> RoiListResponse:
    category_filter = _normalize_text(category)
    search_filter = _normalize_text(search)
    roi_max_filter = roi_max
    if roi_max_filter is None and observe_only:
        roi_max_filter = OBSERVE_ONLY_THRESHOLD

    safe_page = _normalize_positive_int(page, 1)
    safe_page_size = _normalize_positive_int(page_size, ROI_DEFAULT_PAGE_SIZE, ROI_MAX_PAGE_SIZE)

    try:
        rows, total = await roi_repository.fetch_roi_rows(
            session,
            roi_min,
            vendor,
            category_filter.lower() if category_filter else None,
            page=safe_page,
            page_size=safe_page_size,
            sort=sort,
            search=search_filter,
            roi_max=roi_max_filter,
        )
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    serialized = [_serialize_roi_row(dict(row)) for row in rows]
    page_total = total if total > 0 else 0
    total_pages = ceil(page_total / safe_page_size) if page_total > 0 else 1
    resolved_page = min(max(safe_page, 1), max(total_pages, 1))
    pagination = PaginationMeta(page=resolved_page, page_size=safe_page_size, total=page_total, total_pages=total_pages)
    return RoiListResponse(items=serialized, pagination=pagination)


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
