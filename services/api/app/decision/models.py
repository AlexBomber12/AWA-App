from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

METADATA = sa.MetaData()

inbox_threads = sa.Table(
    "inbox_threads",
    METADATA,
    sa.Column("thread_id", sa.Text(), primary_key=True),
    sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id"), nullable=True),
    sa.Column("class", sa.String(length=64), nullable=True),
    sa.Column("state", sa.String(length=32), nullable=False, server_default=sa.text("'open'")),
    sa.Column("last_msg_at", sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column("last_cls", sa.String(length=64), nullable=True),
    sa.Column("assignee", sa.String(length=120), nullable=True),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.Column(
        "updated_at",
        sa.TIMESTAMP(timezone=True),
        server_default=sa.text("now()"),
        server_onupdate=sa.text("now()"),
        nullable=False,
    ),
)

tasks = sa.Table(
    "tasks",
    METADATA,
    sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        primary_key=True,
    ),
    sa.Column("source", sa.String(length=64), nullable=False),
    sa.Column("entity_type", sa.String(length=32), nullable=True),
    sa.Column("asin", sa.String(length=32), nullable=True),
    sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id"), nullable=True),
    sa.Column("thread_id", sa.Text(), sa.ForeignKey("inbox_threads.thread_id"), nullable=True),
    sa.Column("entity", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    sa.Column("summary", sa.Text(), nullable=True),
    sa.Column("decision", sa.String(length=64), nullable=False),
    sa.Column("priority", sa.SmallInteger(), nullable=False, server_default=sa.text("50")),
    sa.Column("deadline_at", sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column("default_action", sa.Text(), nullable=True),
    sa.Column("why", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
    sa.Column(
        "alternatives",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    ),
    sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column("next_request_at", sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column("state", sa.String(length=32), nullable=False, server_default=sa.text("'pending'")),
    sa.Column("assignee", sa.String(length=120), nullable=True),
    sa.Column(
        "links",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text("'{}'::jsonb"),
    ),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.Column(
        "updated_at",
        sa.TIMESTAMP(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
        server_onupdate=sa.text("now()"),
    ),
)

events = sa.Table(
    "events",
    METADATA,
    sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
    sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id"), nullable=True),
    sa.Column("message_id", sa.Text(), nullable=True),
    sa.Column("type", sa.String(length=64), nullable=False),
    sa.Column(
        "meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'::jsonb")
    ),
    sa.Column("ts", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
)

sa.Index("ix_inbox_threads_state", inbox_threads.c.state)
sa.Index("ix_inbox_threads_vendor_id", inbox_threads.c.vendor_id)
sa.Index("ix_inbox_threads_last_msg_at", inbox_threads.c.last_msg_at)

sa.Index("ix_tasks_state_priority_deadline", tasks.c.state, tasks.c.priority, tasks.c.deadline_at)
sa.Index(
    "ix_tasks_state_priority_deadline_created",
    tasks.c.state,
    tasks.c.priority.desc(),
    tasks.c.deadline_at.asc().nullslast(),
    tasks.c.created_at.desc(),
    tasks.c.id,
)
sa.Index(
    "ix_tasks_priority_deadline_created",
    tasks.c.priority.desc(),
    tasks.c.deadline_at.asc().nullslast(),
    tasks.c.created_at.desc(),
    tasks.c.id,
)
sa.Index("ix_tasks_assignee_state", tasks.c.assignee, tasks.c.state)
sa.Index("ix_tasks_asin_vendor", tasks.c.asin, tasks.c.vendor_id)

sa.Index("ix_events_message_id", events.c.message_id)
sa.Index("ix_events_ts", events.c.ts)

inbox_messages = sa.Table(
    "inbox_messages",
    METADATA,
    sa.Column("message_id", sa.Text(), primary_key=True),
    sa.Column("thread_id", sa.Text(), sa.ForeignKey("inbox_threads.thread_id"), nullable=False),
    sa.Column("subject", sa.Text(), nullable=True),
    sa.Column("sender", sa.Text(), nullable=True),
    sa.Column(
        "recipients",
        postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    ),
    sa.Column("body", sa.Text(), nullable=True),
    sa.Column("has_price_list_attachment", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    sa.Column("language", sa.String(length=8), nullable=True),
    sa.Column("intent", sa.String(length=64), nullable=True),
    sa.Column("facts", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'::jsonb")),
    sa.Column("llm_provider", sa.String(length=32), nullable=True),
    sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
    sa.Column("needs_manual_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    sa.Column("error", sa.Text(), nullable=True),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.Column(
        "updated_at",
        sa.TIMESTAMP(timezone=True),
        server_default=sa.text("now()"),
        server_onupdate=sa.text("now()"),
        nullable=False,
    ),
)
sa.Index("ix_inbox_messages_intent", inbox_messages.c.intent)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_json(value: Any, fallback: Any) -> Any:
    if value is None:
        return fallback
    return value


def _normalize_reason(item: Any) -> dict[str, Any]:
    if item is None:
        return {}
    if isinstance(item, str):
        return {"code": "info", "message": item}
    if isinstance(item, Mapping):
        code = str(item.get("code") or "info")
        message = item.get("message") or item.get("detail") or item.get("title") or ""
        data = item.get("data") or {}
        if isinstance(data, Mapping):
            data = dict(data)
        metric = item.get("metric")
        if not message:
            message = code
        if item.get("detail") and isinstance(data, dict) and "detail" not in data:
            data = {**data, "detail": item.get("detail")}
        if metric is not None:
            try:
                metric_value = float(metric) if not isinstance(metric, str) else metric
            except (TypeError, ValueError):
                metric_value = metric
            data = {**(data or {}), "metric": metric_value}
        payload: dict[str, Any] = {"code": code, "message": str(message)}
        if data:
            payload["data"] = data
        if metric is not None:
            payload["metric"] = metric
        return payload
    return {"code": "info", "message": str(item)}


def normalize_reasons(items: Sequence[Any] | None) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    if not items:
        return reasons
    is_sequence = isinstance(items, Sequence) and not isinstance(items, (str, Mapping))
    items_iterable: Sequence[Any] = items if is_sequence else [items]
    for item in items_iterable:
        normalized = _normalize_reason(item)
        if normalized:
            reasons.append(normalized)
    return reasons


def _normalize_alternative(item: Any) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        return {"action": str(item)}
    action = item.get("action") or item.get("decision") or item.get("code") or "unspecified"
    payload: dict[str, Any] = {"action": str(action)}
    for key in ("label", "impact"):
        value = item.get(key)
        if value is not None:
            payload[key] = value
    confidence = item.get("confidence")
    try:
        if confidence is not None:
            payload["confidence"] = float(confidence)
    except (TypeError, ValueError):
        pass
    nested_reasons = item.get("why") or item.get("reasons")
    reasons = normalize_reasons(nested_reasons if isinstance(nested_reasons, Sequence) else None)
    if reasons:
        payload["why"] = reasons
    return payload


def normalize_alternatives(items: Sequence[Any] | None) -> list[dict[str, Any]]:
    alternatives: list[dict[str, Any]] = []
    if not items:
        return alternatives
    is_sequence = isinstance(items, Sequence) and not isinstance(items, (str, Mapping))
    items_iterable: Sequence[Any] = items if is_sequence else [items]
    for item in items_iterable:
        normalized = _normalize_alternative(item)
        if normalized:
            alternatives.append(normalized)
    return alternatives


def normalize_links(data: Mapping[str, Any]) -> dict[str, Any]:
    links_raw = _parse_json(data.get("links"), {}) or {}
    allowed_keys = {
        "asin",
        "vendor_id",
        "thread_id",
        "entity_type",
        "campaign_id",
        "price_list_row_id",
        "entity_id",
        "category",
    }
    merged: dict[str, Any] = {}
    if isinstance(links_raw, Mapping):
        for key, value in links_raw.items():
            if value is not None and str(key) in allowed_keys:
                merged[str(key)] = value
    for key in ("asin", "vendor_id", "thread_id", "entity_type"):
        value = data.get(key)
        if value is not None and key not in merged:
            merged[key] = value
    entity = data.get("entity")
    if isinstance(entity, Mapping):
        asin = entity.get("asin")
        vendor_id = entity.get("vendor_id")
        campaign_id = entity.get("campaign_id")
        price_list_row_id = entity.get("price_list_row_id")
        entity_id = entity.get("entity_id")
        if asin is not None:
            merged.setdefault("asin", asin)
        if vendor_id is not None:
            merged.setdefault("vendor_id", vendor_id)
        if campaign_id is not None:
            merged.setdefault("campaign_id", campaign_id)
        if price_list_row_id is not None:
            merged.setdefault("price_list_row_id", price_list_row_id)
        if entity_id is not None:
            merged.setdefault("entity_id", entity_id)
    return merged


@dataclass(slots=True)
class DecisionCandidate:
    asin: str
    vendor_id: int | None
    cost: float | None
    roi_pct: float | None
    category: str | None = None
    observe_only: bool = False
    buybox_price: float | None = None
    fees: float | None = None
    risk_adjusted_roi: float | None = None


@dataclass(slots=True)
class PlannedDecisionTask:
    asin: str
    vendor_id: int | None
    decision: str
    priority: int
    summary: str
    default_action: str | None
    why: list[Any]
    alternatives: list[Any]
    source: str = "decision_engine"
    entity_type: str | None = None
    entity: dict[str, Any] = field(default_factory=dict)
    deadline_at: datetime | None = None
    next_request_at: datetime | None = None
    state: str = "pending"
    metrics: dict[str, Any] | None = None
    thread_id: str | None = None
    assignee: str | None = None
    links: dict[str, Any] | None = None


@dataclass(slots=True)
class DecisionTaskRecord:
    id: str
    source: str
    entity: dict[str, Any]
    decision: str
    priority: int
    state: str
    summary: str | None = None
    entity_type: str | None = None
    asin: str | None = None
    vendor_id: int | None = None
    thread_id: str | None = None
    deadline_at: datetime | None = None
    default_action: str | None = None
    why: list[Any] = field(default_factory=list)
    alternatives: list[Any] = field(default_factory=list)
    metrics: dict[str, Any] | None = None
    next_request_at: datetime | None = None
    assignee: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    links: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> DecisionTaskRecord:
        def _uuid_to_str(value: Any) -> str:
            if value is None:
                return ""
            return str(value)

        return cls(
            id=_uuid_to_str(data.get("id")),
            source=str(data.get("source") or ""),
            entity=dict(data.get("entity") or {}),
            decision=str(data.get("decision") or ""),
            priority=int(data.get("priority") or 0),
            state=str(data.get("state") or ""),
            summary=data.get("summary"),
            entity_type=data.get("entity_type"),
            asin=data.get("asin"),
            vendor_id=data.get("vendor_id"),
            thread_id=data.get("thread_id"),
            deadline_at=data.get("deadline_at"),
            default_action=data.get("default_action"),
            why=normalize_reasons(_parse_json(data.get("why"), []) or []),
            alternatives=normalize_alternatives(_parse_json(data.get("alternatives"), []) or []),
            metrics=_parse_json(data.get("metrics"), None),
            next_request_at=data.get("next_request_at"),
            assignee=data.get("assignee"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            links=normalize_links(data),
        )


@dataclass(slots=True)
class DecisionEventRecord:
    id: int
    task_id: str | None
    type: str
    meta_json: dict[str, Any] | None
    ts: datetime | None = None
    message_id: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> DecisionEventRecord:
        def _uuid_to_str(value: Any) -> str | None:
            if value is None:
                return None
            return str(value)

        return cls(
            id=int(data.get("id") or 0),
            task_id=_uuid_to_str(data.get("task_id")),
            type=str(data.get("type") or ""),
            meta_json=_parse_json(data.get("meta_json"), {}) or {},
            ts=data.get("ts"),
            message_id=data.get("message_id"),
        )


@dataclass(slots=True)
class InboxMessageRecord:
    message_id: str
    thread_id: str
    subject: str | None
    sender: str | None
    recipients: list[Any]
    intent: str | None
    facts: dict[str, Any] | None
    llm_provider: str | None
    confidence: float | None
    needs_manual_review: bool
    error: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> InboxMessageRecord:  # pragma: no cover - simple mapper
        return cls(
            message_id=str(data.get("message_id") or ""),
            thread_id=str(data.get("thread_id") or ""),
            subject=data.get("subject"),
            sender=data.get("sender"),
            recipients=list(_parse_json(data.get("recipients"), [])),
            intent=data.get("intent"),
            facts=_parse_json(data.get("facts"), {}) or {},
            llm_provider=data.get("llm_provider"),
            confidence=_to_float(data.get("confidence")),
            needs_manual_review=bool(data.get("needs_manual_review")),
            error=data.get("error"),
        )


__all__: Sequence[str] = [  # pragma: no cover - export list only
    "DecisionCandidate",
    "DecisionEventRecord",
    "DecisionTaskRecord",
    "InboxMessageRecord",
    "METADATA",
    "PlannedDecisionTask",
    "events",
    "inbox_messages",
    "inbox_threads",
    "normalize_alternatives",
    "normalize_links",
    "normalize_reasons",
    "tasks",
]
