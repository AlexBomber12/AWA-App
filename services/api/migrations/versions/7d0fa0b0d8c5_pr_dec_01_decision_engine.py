from __future__ import annotations

import sqlalchemy as sa
from alembic import op  # type: ignore[attr-defined]
from sqlalchemy.dialects import postgresql

revision = "7d0fa0b0d8c5"
down_revision = "6f4b9f9c8b21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "inbox_threads",
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
    op.create_index("ix_inbox_threads_state", "inbox_threads", ["state"])
    op.create_index("ix_inbox_threads_vendor_id", "inbox_threads", ["vendor_id"])
    op.create_index("ix_inbox_threads_last_msg_at", "inbox_threads", ["last_msg_at"])

    op.create_table(
        "tasks",
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
        sa.Column(
            "entity", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("decision", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.SmallInteger(), nullable=False, server_default=sa.text("50")),
        sa.Column("deadline_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("default_action", sa.Text(), nullable=True),
        sa.Column(
            "why", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
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
            server_onupdate=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_tasks_state_priority_deadline", "tasks", ["state", "priority", "deadline_at"])
    op.create_index("ix_tasks_assignee_state", "tasks", ["assignee", "state"])
    op.create_index("ix_tasks_asin_vendor", "tasks", ["asin", "vendor_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("message_id", sa.Text(), nullable=True),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column(
            "meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("ts", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_events_message_id", "events", ["message_id"])
    op.create_index("ix_events_ts", "events", ["ts"])


def downgrade() -> None:
    op.drop_index("ix_events_ts", table_name="events")
    op.drop_index("ix_events_message_id", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_tasks_asin_vendor", table_name="tasks")
    op.drop_index("ix_tasks_assignee_state", table_name="tasks")
    op.drop_index("ix_tasks_state_priority_deadline", table_name="tasks")
    op.drop_table("tasks")

    op.drop_index("ix_inbox_threads_last_msg_at", table_name="inbox_threads")
    op.drop_index("ix_inbox_threads_vendor_id", table_name="inbox_threads")
    op.drop_index("ix_inbox_threads_state", table_name="inbox_threads")
    op.drop_table("inbox_threads")
