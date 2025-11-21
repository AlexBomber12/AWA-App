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
sa.Index("ix_tasks_assignee_state", tasks.c.assignee, tasks.c.state)
sa.Index("ix_tasks_asin_vendor", tasks.c.asin, tasks.c.vendor_id)

sa.Index("ix_events_message_id", events.c.message_id)
sa.Index("ix_events_ts", events.c.ts)


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
            why=list(_parse_json(data.get("why"), [])),
            alternatives=list(_parse_json(data.get("alternatives"), [])),
            metrics=_parse_json(data.get("metrics"), None),
            next_request_at=data.get("next_request_at"),
            assignee=data.get("assignee"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
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


__all__: Sequence[str] = [
    "DecisionCandidate",
    "DecisionEventRecord",
    "DecisionTaskRecord",
    "METADATA",
    "PlannedDecisionTask",
    "events",
    "inbox_threads",
    "tasks",
]
