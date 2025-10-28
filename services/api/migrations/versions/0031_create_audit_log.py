from __future__ import annotations

from textwrap import dedent

from alembic import op  # type: ignore[attr-defined]

revision = "0031_create_audit_log"
down_revision = "0030_logistics_rates_and_loadlog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        dedent(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id BIGSERIAL PRIMARY KEY,
                ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                user_id TEXT,
                email TEXT,
                roles TEXT[],
                method TEXT,
                path TEXT,
                route TEXT,
                status INT,
                latency_ms INT,
                ip TEXT,
                ua TEXT,
                request_id TEXT
            );
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE INDEX IF NOT EXISTS ix_audit_log_ts
                ON audit_log (ts);
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE INDEX IF NOT EXISTS ix_audit_log_user_id
                ON audit_log (user_id);
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE INDEX IF NOT EXISTS ix_audit_log_route_ts_desc
                ON audit_log (route, ts DESC);
            """
        )
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_log;")
