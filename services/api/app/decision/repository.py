from __future__ import annotations

import datetime as dt
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy import TextClause
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.app.decision.models import (
    DecisionCandidate,
    DecisionTaskRecord,
    PlannedDecisionTask,
    events,
    normalize_alternatives,
    normalize_reasons,
    tasks,
)
from services.api.roi_views import get_roi_view_name, quote_identifier

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 200
DECISION_SOURCE = "decision_engine"
DEFAULT_GENERATION_LIMIT = 200
PENDING_STATES: tuple[str, ...] = ("pending", "snoozed")


def _roi_candidate_sql(view_name: str) -> TextClause:
    quoted = quote_identifier(view_name)
    return sa.text(
        f"""
        SELECT
            p.asin,
            vp.vendor_id,
            vp.cost,
            vf.roi_pct,
            p.category,
            vf.buybox_price,
            vf.fees
        FROM {quoted} vf
        JOIN products p ON p.asin = vf.asin
        LEFT JOIN LATERAL (
            SELECT vendor_id, cost
            FROM vendor_prices
            WHERE sku = p.asin
            ORDER BY updated_at DESC
            LIMIT 1
        ) vp ON TRUE
        WHERE vf.roi_pct IS NOT NULL
        ORDER BY vf.roi_pct ASC NULLS LAST, p.asin ASC
        LIMIT :limit
        """
    )


async def fetch_decision_candidates(
    session: AsyncSession,
    *,
    limit: int = DEFAULT_GENERATION_LIMIT,
) -> list[DecisionCandidate]:
    view_name = get_roi_view_name()
    stmt = _roi_candidate_sql(view_name)
    result = await session.execute(stmt, {"limit": limit})
    rows = result.mappings().all()
    candidates: list[DecisionCandidate] = []
    for row in rows:
        candidates.append(
            DecisionCandidate(
                asin=str(row.get("asin") or ""),
                vendor_id=row.get("vendor_id"),
                cost=_to_float(row.get("cost")),
                roi_pct=_to_float(row.get("roi_pct")),
                category=row.get("category"),
                buybox_price=_to_float(row.get("buybox_price")),
                fees=_to_float(row.get("fees")),
            )
        )
    return candidates


def _normalize_page(page: int | None) -> int:
    if page is None or page < 1:
        return 1
    return page


def _normalize_page_size(page_size: int | None) -> int:
    if page_size is None or page_size < 1:
        return DEFAULT_PAGE_SIZE
    return min(page_size, MAX_PAGE_SIZE)


def _sort_clause(sort: str | None) -> Sequence[Any]:
    sort_key = (sort or "priority").lower()
    if sort_key == "deadline":
        return (
            tasks.c.deadline_at.asc().nullslast(),
            tasks.c.priority.desc(),
            tasks.c.created_at.desc(),
            tasks.c.id.asc(),
        )
    if sort_key == "created_at":
        return (tasks.c.created_at.desc(), tasks.c.id.desc())
    return (
        tasks.c.priority.desc(),
        tasks.c.deadline_at.asc().nullslast(),
        tasks.c.created_at.desc(),
        tasks.c.id.asc(),
    )


def _normalize_state(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.lower()
    state_map = {
        "open": "pending",
        "pending": "pending",
        "done": "applied",
        "resolved": "applied",
        "applied": "applied",
        "dismissed": "dismissed",
        "cancelled": "dismissed",
        "blocked": "expired",
        "expired": "expired",
        "snoozed": "snoozed",
        "in_progress": "snoozed",
    }
    return state_map.get(normalized, normalized)


def _task_filters(
    *,
    state: str | None = None,
    source: str | None = None,
    priority: int | None = None,
    assignee: str | None = None,
    search: str | None = None,
    task_id: str | None = None,
) -> list[Any]:
    conditions: list[Any] = []
    state_filter = _normalize_state(state)
    if state_filter and state_filter != "all":
        conditions.append(tasks.c.state == state_filter)
    if source:
        conditions.append(tasks.c.source == source)
    if priority is not None:
        conditions.append(tasks.c.priority >= priority)
    if assignee:
        conditions.append(tasks.c.assignee == assignee)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            sa.or_(
                tasks.c.summary.ilike(pattern),
                tasks.c.asin.ilike(pattern),
                tasks.c.decision.ilike(pattern),
            )
        )
    if task_id:
        conditions.append(tasks.c.id == task_id)
    return conditions


async def list_tasks(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    state: str | None = None,
    source: str | None = None,
    priority: int | None = None,
    assignee: str | None = None,
    search: str | None = None,
    task_id: str | None = None,
    sort: str | None = None,
) -> tuple[list[DecisionTaskRecord], int, dict[str, int]]:
    safe_page = _normalize_page(page)
    safe_page_size = _normalize_page_size(page_size)
    offset = (safe_page - 1) * safe_page_size
    conditions = _task_filters(
        state=state,
        source=source,
        priority=priority,
        assignee=assignee,
        search=search,
        task_id=task_id,
    )

    stmt = sa.select(tasks).where(*conditions).order_by(*_sort_clause(sort)).limit(safe_page_size).offset(offset)
    rows = (await session.execute(stmt)).mappings().all()
    items = [DecisionTaskRecord.from_mapping(dict(row)) for row in rows]

    total_stmt = sa.select(sa.func.count()).select_from(tasks).where(*conditions)
    total_result = await session.execute(total_stmt)
    scalar_fn = getattr(total_result, "scalar_one", None)
    if callable(scalar_fn):
        total_value = scalar_fn()
    else:
        total_value = total_result.scalar()
    total = int(total_value or 0)

    summary = await summarize_states(session, conditions)
    return items, total, summary


async def summarize_states(session: AsyncSession, conditions: Iterable[Any]) -> dict[str, int]:
    stmt = sa.select(tasks.c.state, sa.func.count().label("count")).where(*conditions).group_by(tasks.c.state)
    result = await session.execute(stmt)
    summary: dict[str, int] = {"pending": 0, "applied": 0, "dismissed": 0, "expired": 0, "snoozed": 0}
    for state, count in result.all():
        summary[str(state)] = int(count or 0)
    return summary


async def fetch_task_by_id(session: AsyncSession, task_id: str) -> DecisionTaskRecord | None:
    stmt = sa.select(tasks).where(tasks.c.id == task_id)
    result = await session.execute(stmt)
    row = result.mappings().first()
    if not row:
        return None
    return DecisionTaskRecord.from_mapping(dict(row))


async def upsert_tasks(
    session: AsyncSession,
    plans: Sequence[PlannedDecisionTask],
    *,
    now: dt.datetime | None = None,
) -> list[DecisionTaskRecord]:
    if not plans:
        return []

    now_ts = now or dt.datetime.now(dt.UTC)
    asins = {plan.asin for plan in plans}
    decisions = {plan.decision for plan in plans}
    vendor_ids = {plan.vendor_id for plan in plans if plan.vendor_id is not None}

    vendor_filter: list[Any] = []
    if vendor_ids:
        vendor_filter.append(sa.or_(tasks.c.vendor_id.in_(vendor_ids), tasks.c.vendor_id.is_(None)))

    existing_stmt = sa.select(tasks).where(
        tasks.c.asin.in_(asins),
        tasks.c.decision.in_(decisions),
        tasks.c.state.in_(PENDING_STATES),
        *vendor_filter,
    )
    existing_rows = (await session.execute(existing_stmt)).mappings().all()
    existing_map: dict[tuple[str | None, int | None, str], Mapping[str, Any]] = {}
    for row in existing_rows:
        row_map: Mapping[str, Any] = dict(row)
        key = (
            cast(str | None, row_map.get("asin")),
            cast(int | None, row_map.get("vendor_id")),
            str(row_map.get("decision") or ""),
        )
        existing_map[key] = row_map

    saved: list[DecisionTaskRecord] = []
    for plan in plans:
        key = (plan.asin, plan.vendor_id, plan.decision)
        links = _links_for_plan(plan)
        payload = {
            "source": plan.source or DECISION_SOURCE,
            "entity_type": plan.entity_type,
            "asin": plan.asin,
            "vendor_id": plan.vendor_id,
            "thread_id": plan.thread_id,
            "entity": plan.entity or _default_entity(plan),
            "summary": plan.summary,
            "decision": plan.decision,
            "priority": plan.priority,
            "deadline_at": plan.deadline_at,
            "default_action": plan.default_action,
            "why": normalize_reasons(plan.why),
            "alternatives": normalize_alternatives(plan.alternatives),
            "links": links,
            "metrics": plan.metrics,
            "next_request_at": plan.next_request_at,
            "state": plan.state,
            "assignee": plan.assignee,
            "updated_at": now_ts,
        }
        existing = existing_map.get(key)
        if existing:
            update_stmt = tasks.update().where(tasks.c.id == existing.get("id")).values(**payload).returning(tasks)
            update_result = await session.execute(update_stmt)
            row = update_result.mappings().first()
        else:
            payload["created_at"] = now_ts
            insert_stmt = tasks.insert().values(**payload).returning(tasks)
            insert_result = await session.execute(insert_stmt)
            row = insert_result.mappings().first()
        if row:
            saved.append(DecisionTaskRecord.from_mapping(dict(row)))

    await session.commit()
    return saved


def _default_entity(plan: PlannedDecisionTask) -> dict[str, Any]:
    entity_type = plan.entity_type or "sku_vendor"
    entity: dict[str, Any] = {"type": entity_type, "asin": plan.asin}
    if plan.vendor_id is not None:
        entity["vendor_id"] = plan.vendor_id
    return entity


def _links_for_plan(plan: PlannedDecisionTask) -> dict[str, Any]:
    links = dict(plan.links or {})
    if plan.asin and "asin" not in links:
        links["asin"] = plan.asin
    if plan.vendor_id is not None and "vendor_id" not in links:
        links["vendor_id"] = plan.vendor_id
    if plan.thread_id and "thread_id" not in links:
        links["thread_id"] = plan.thread_id
    if plan.entity_type and "entity_type" not in links:
        links["entity_type"] = plan.entity_type
    entity = plan.entity or {}
    if isinstance(entity, Mapping):
        for key in ("asin", "vendor_id", "campaign_id", "price_list_row_id", "entity_id"):
            value = entity.get(key)
            if value is not None and key not in links:
                links[key] = value
    return links


async def update_task_state(
    session: AsyncSession,
    task_id: str,
    new_state: str,
    *,
    actor: str | None = None,
    note: str | None = None,
    next_request_at: dt.datetime | None = None,
    event_type: str | None = None,
) -> DecisionTaskRecord | None:
    current = await fetch_task_by_id(session, task_id)
    if current is None:
        return None

    update_payload: dict[str, Any] = {
        "state": new_state,
        "updated_at": dt.datetime.now(dt.UTC),
    }
    if next_request_at is not None:
        update_payload["next_request_at"] = next_request_at

    stmt = tasks.update().where(tasks.c.id == task_id).values(**update_payload).returning(tasks)
    result = await session.execute(stmt)
    updated_row = result.mappings().first()
    if not updated_row:
        await session.rollback()
        return None

    await session.execute(
        events.insert().values(
            task_id=task_id,
            type=event_type or new_state,
            meta_json={
                "actor": actor,
                "note": note,
                "prev_state": current.state,
                "new_state": new_state,
            },
        )
    )
    await session.commit()
    return DecisionTaskRecord.from_mapping(updated_row)


async def insert_event(
    session: AsyncSession,
    *,
    task_id: str | None,
    event_type: str,
    meta: dict[str, Any] | None = None,
    message_id: str | None = None,
) -> None:
    await session.execute(
        events.insert().values(
            task_id=task_id,
            type=event_type,
            meta_json=meta or {},
            message_id=message_id,
        )
    )
    await session.commit()


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "DECISION_SOURCE",
    "DEFAULT_GENERATION_LIMIT",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "fetch_decision_candidates",
    "fetch_task_by_id",
    "insert_event",
    "list_tasks",
    "summarize_states",
    "update_task_state",
    "upsert_tasks",
]
