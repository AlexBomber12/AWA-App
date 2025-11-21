from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.db.async_session import get_async_session
from awa_common.security.models import UserCtx
from services.api.app.decision import repository, service
from services.api.app.decision.models import DecisionTaskRecord, PlannedDecisionTask
from services.api.roi_views import InvalidROIViewError
from services.api.routes.decision_serializers import derive_summary, serialize_planned, serialize_task
from services.api.schemas import DecisionPreviewResponse, DecisionTaskListResponse, PaginationMeta
from services.api.security import limit_ops, require_admin

router = APIRouter(prefix="/decision", tags=["decision"])


@router.get("/preview", response_model=DecisionPreviewResponse)
async def preview_decisions(
    limit: int = Query(repository.DEFAULT_GENERATION_LIMIT, ge=1, le=repository.DEFAULT_GENERATION_LIMIT),
    session: AsyncSession = Depends(get_async_session),
    user: UserCtx = Depends(require_admin),
    _limit: None = Depends(limit_ops),
) -> DecisionPreviewResponse:
    saved: list[DecisionTaskRecord] = []
    planned: list[PlannedDecisionTask] = []
    candidates = 0
    try:
        saved, planned, candidates = await service.generate_tasks(session, limit=limit, dry_run=True)
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    planned_payload = [serialize_planned(task, idx) for idx, task in enumerate(planned)]
    return DecisionPreviewResponse(planned=planned_payload, generated=len(planned_payload), candidates=candidates)


@router.post("/run", response_model=DecisionTaskListResponse)
async def run_decision_engine(
    limit: int = Query(repository.DEFAULT_GENERATION_LIMIT, ge=1, le=repository.DEFAULT_GENERATION_LIMIT),
    session: AsyncSession = Depends(get_async_session),
    user: UserCtx = Depends(require_admin),
    _limit: None = Depends(limit_ops),
) -> DecisionTaskListResponse:
    saved: list[DecisionTaskRecord] = []
    try:
        saved, _, _ = await service.generate_tasks(session, limit=limit, dry_run=False)
    except InvalidROIViewError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    items = [serialize_task(task) for task in saved]
    total = len(items)
    page_size = max(1, total) or 1
    pagination = PaginationMeta(
        page=1,
        page_size=page_size,
        total=total,
        total_pages=max(1, math.ceil(total / page_size)),
    )
    summary = derive_summary(await repository.summarize_states(session, []))
    return DecisionTaskListResponse(items=items, pagination=pagination, summary=summary)
