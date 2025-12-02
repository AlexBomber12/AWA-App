from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from awa_common.db.async_session import get_async_session
from awa_common.security.models import UserCtx
from services.api.app.decision import repository, service
from services.api.routes.decision_serializers import derive_summary, serialize_task
from services.api.schemas import DecisionTask, DecisionTaskListResponse, PaginationMeta, TaskUpdateRequest
from services.api.security import limit_ops, require_ops

router = APIRouter(prefix="/inbox", tags=["inbox"])


def _resolve_actor(user: UserCtx | None) -> str | None:
    if user is None:
        return None
    for attr in ("email", "sub"):
        value = getattr(user, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


@router.get("/tasks", response_model=DecisionTaskListResponse)
async def list_inbox_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(repository.DEFAULT_PAGE_SIZE, ge=1, le=repository.MAX_PAGE_SIZE, alias="pageSize"),
    state: str | None = Query(None),
    status: str | None = Query(None),
    source: str | None = Query(None),
    priority: int | None = Query(None),
    assignee: str | None = Query(None),
    search: str | None = Query(None),
    task_id: str | None = Query(None, alias="taskId"),
    sort: str | None = Query("priority"),
    session: AsyncSession = Depends(get_async_session),
    user: UserCtx = Depends(require_ops),
    _limit: None = Depends(limit_ops),
) -> DecisionTaskListResponse:
    _ = user  # unused but ensures RBAC
    state_filter = status or state
    items, total, summary = await repository.list_tasks(
        session,
        page=page,
        page_size=page_size,
        state=state_filter,
        source=source,
        priority=priority,
        assignee=assignee,
        search=search,
        task_id=task_id,
        sort=sort,
    )
    total_pages = max(1, math.ceil(total / page_size))
    pagination = PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)
    serialized = [serialize_task(item) for item in items]
    return DecisionTaskListResponse(items=serialized, pagination=pagination, summary=derive_summary(summary))


@router.post("/tasks/{task_id}/apply", response_model=DecisionTask)
async def apply_task(
    task_id: str,
    body: TaskUpdateRequest | None = None,
    session: AsyncSession = Depends(get_async_session),
    user: UserCtx = Depends(require_ops),
    _limit: None = Depends(limit_ops),
) -> DecisionTask:
    note = body.note if body else None
    updated = await service.apply_task(session, task_id, actor=_resolve_actor(user), note=note)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return serialize_task(updated)


@router.post("/tasks/{task_id}/dismiss", response_model=DecisionTask)
async def dismiss_task(
    task_id: str,
    body: TaskUpdateRequest | None = None,
    session: AsyncSession = Depends(get_async_session),
    user: UserCtx = Depends(require_ops),
    _limit: None = Depends(limit_ops),
) -> DecisionTask:
    note = body.note if body else None
    updated = await service.dismiss_task(
        session,
        task_id,
        actor=_resolve_actor(user),
        note=note,
        next_request_at=body.next_request_at if body else None,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return serialize_task(updated)
