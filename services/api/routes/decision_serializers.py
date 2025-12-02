from __future__ import annotations

from collections.abc import Sequence

from services.api.app.decision.models import (
    DecisionTaskRecord,
    PlannedDecisionTask,
    normalize_alternatives,
    normalize_links,
    normalize_reasons,
)
from services.api.schemas import (
    DecisionAlternative,
    DecisionLinks,
    DecisionReason,
    DecisionTask,
    DecisionTaskSummary,
)

_STATE_MAP = {
    "pending": "open",
    "snoozed": "in_progress",
    "applied": "done",
    "dismissed": "cancelled",
    "expired": "blocked",
}


def _links_from_record(
    *,
    asin: str | None,
    vendor_id: int | None,
    thread_id: str | None,
    entity_type: str | None,
    links: dict[str, object] | None,
    entity: dict[str, object] | None,
) -> dict[str, object]:
    return normalize_links(
        {
            "asin": asin,
            "vendor_id": vendor_id,
            "thread_id": thread_id,
            "entity_type": entity_type,
            "links": links or {},
            "entity": entity or {},
        }
    )


def _typed_reasons(raw: Sequence[object] | None) -> list[DecisionReason]:
    normalized = normalize_reasons(raw)
    return [DecisionReason(**reason) for reason in normalized]


def _typed_alternatives(raw: Sequence[object] | None) -> list[DecisionAlternative]:
    normalized = normalize_alternatives(raw)
    typed: list[DecisionAlternative] = []
    for alt in normalized:
        alt_map = dict(alt)
        nested = alt_map.pop("why", [])
        typed.append(
            DecisionAlternative(
                action=str(alt_map.get("action") or ""),
                label=alt_map.get("label"),
                impact=alt_map.get("impact"),
                confidence=alt_map.get("confidence"),
                why=_typed_reasons(nested if isinstance(nested, Sequence) else []),
            )
        )
    return typed


def serialize_task(record: DecisionTaskRecord) -> DecisionTask:
    state = _STATE_MAP.get(record.state, record.state)
    links = _links_from_record(
        asin=record.asin,
        vendor_id=record.vendor_id,
        thread_id=record.thread_id,
        entity_type=record.entity_type,
        links=record.links,
        entity=record.entity,
    )
    return DecisionTask(
        id=str(record.id),
        source=record.source,
        entity=record.entity,
        decision=record.decision,
        priority=int(record.priority),
        deadline_at=record.deadline_at,
        default_action=record.default_action,
        why=_typed_reasons(record.why),
        alternatives=_typed_alternatives(record.alternatives),
        next_request_at=record.next_request_at,
        state=state,
        status=state,
        assignee=record.assignee,
        summary=record.summary,
        metrics=record.metrics,
        created_at=record.created_at,
        updated_at=record.updated_at,
        links=DecisionLinks.model_validate(links) if isinstance(links, dict) else DecisionLinks(),
    )


def serialize_planned(task: PlannedDecisionTask, idx: int) -> DecisionTask:
    surrogate_id = f"planned-{idx}-{task.asin}"
    state = _STATE_MAP.get(task.state, task.state)
    links = _links_from_record(
        asin=task.asin,
        vendor_id=task.vendor_id,
        thread_id=task.thread_id,
        entity_type=task.entity_type,
        links=task.links,
        entity=task.entity,
    )
    return DecisionTask(
        id=surrogate_id,
        source=task.source,
        entity=task.entity,
        decision=task.decision,
        priority=int(task.priority),
        deadline_at=task.deadline_at,
        default_action=task.default_action,
        why=_typed_reasons(task.why),
        alternatives=_typed_alternatives(task.alternatives),
        next_request_at=task.next_request_at,
        state=state,
        status=state,
        assignee=task.assignee,
        summary=task.summary,
        metrics=task.metrics,
        created_at=None,
        updated_at=None,
        links=DecisionLinks.model_validate(links) if isinstance(links, dict) else DecisionLinks(),
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
