from __future__ import annotations

from services.api.app.decision.models import DecisionTaskRecord, PlannedDecisionTask
from services.api.schemas import DecisionTask, DecisionTaskSummary

_STATE_MAP = {
    "pending": "open",
    "snoozed": "in_progress",
    "applied": "done",
    "dismissed": "cancelled",
    "expired": "blocked",
}


def serialize_task(record: DecisionTaskRecord) -> DecisionTask:
    state = _STATE_MAP.get(record.state, record.state)
    return DecisionTask(
        id=str(record.id),
        source=record.source,
        entity=record.entity,
        decision=record.decision,
        priority=int(record.priority),
        deadline_at=record.deadline_at,
        default_action=record.default_action,
        why=list(record.why or []),
        alternatives=list(record.alternatives or []),
        next_request_at=record.next_request_at,
        state=state,
        assignee=record.assignee,
        summary=record.summary,
        metrics=record.metrics,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def serialize_planned(task: PlannedDecisionTask, idx: int) -> DecisionTask:
    surrogate_id = f"planned-{idx}-{task.asin}"
    state = _STATE_MAP.get(task.state, task.state)
    return DecisionTask(
        id=surrogate_id,
        source=task.source,
        entity=task.entity,
        decision=task.decision,
        priority=int(task.priority),
        deadline_at=task.deadline_at,
        default_action=task.default_action,
        why=list(task.why or []),
        alternatives=list(task.alternatives or []),
        next_request_at=task.next_request_at,
        state=state,
        assignee=task.assignee,
        summary=task.summary,
        metrics=task.metrics,
        created_at=None,
        updated_at=None,
    )


def derive_summary(raw: dict[str, int]) -> DecisionTaskSummary:
    pending = raw.get("pending", 0)
    snoozed = raw.get("snoozed", 0)
    expired = raw.get("expired", 0)
    return DecisionTaskSummary(
        pending=pending,
        applied=raw.get("applied", 0),
        dismissed=raw.get("dismissed", 0),
        expired=expired,
        snoozed=snoozed,
        open=pending,
        in_progress=snoozed,
        blocked=expired,
    )


__all__ = ["derive_summary", "serialize_planned", "serialize_task"]
