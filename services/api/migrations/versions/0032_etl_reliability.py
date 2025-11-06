from __future__ import annotations

from textwrap import dedent

import sqlalchemy as sa
from alembic import op  # type: ignore[attr-defined]

revision = "0032_etl_reliability"
down_revision = "0031_create_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_load_log_updated_at ON load_log;")
    op.execute("DROP FUNCTION IF EXISTS set_load_log_updated_at();")
    op.execute("DROP TABLE IF EXISTS load_log;")

    op.create_table(
        "load_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "payload_meta",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("processed_by", sa.String(length=64), nullable=True),
        sa.Column("task_id", sa.String(length=64), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('pending','success','skipped','failed')",
            name="ck_load_log_status",
        ),
        sa.UniqueConstraint("source", "idempotency_key", name="uq_load_log_source_key"),
    )
    op.create_index("ix_load_log_created_at", "load_log", ["created_at"], unique=False)

    op.execute(
        dedent(
            """
            CREATE OR REPLACE FUNCTION set_load_log_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )
    op.execute(
        """
        CREATE TRIGGER trg_load_log_updated_at
        BEFORE UPDATE ON load_log
        FOR EACH ROW
        EXECUTE FUNCTION set_load_log_updated_at();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_load_log_updated_at ON load_log;")
    op.execute("DROP FUNCTION IF EXISTS set_load_log_updated_at();")
    op.drop_index("ix_load_log_created_at", table_name="load_log")
    op.drop_table("load_log")
