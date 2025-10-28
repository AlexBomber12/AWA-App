from __future__ import annotations

from textwrap import dedent

from alembic import op  # type: ignore[attr-defined]

revision = "0030_logistics_rates_and_loadlog"
down_revision = "0029_price_updates_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        dedent(
            """
            CREATE TABLE IF NOT EXISTS logistics_rates (
                carrier TEXT NOT NULL,
                origin TEXT NOT NULL,
                dest TEXT NOT NULL,
                service TEXT NOT NULL,
                eur_per_kg NUMERIC(10, 4) NOT NULL,
                effective_from DATE,
                effective_to DATE,
                source TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_logistics_rates_lane_service
                ON logistics_rates (
                    carrier,
                    origin,
                    dest,
                    service,
                    COALESCE(effective_from, DATE '1900-01-01')
                );
            """
        )
    )

    op.execute(
        dedent(
            """
            CREATE TABLE IF NOT EXISTS logistics_loadlog (
                id BIGSERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                sha256 TEXT,
                seqno TEXT,
                rows INT NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_logistics_loadlog_source_sha256
                ON logistics_loadlog (source, sha256)
                WHERE sha256 IS NOT NULL;
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_logistics_loadlog_source_seqno
                ON logistics_loadlog (source, seqno)
                WHERE seqno IS NOT NULL;
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE INDEX IF NOT EXISTS ix_logistics_loadlog_created_at
                ON logistics_loadlog (created_at DESC);
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE INDEX IF NOT EXISTS ix_logistics_loadlog_source
                ON logistics_loadlog (source);
            """
        )
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS logistics_loadlog;")
    op.execute("DROP TABLE IF EXISTS logistics_rates;")
