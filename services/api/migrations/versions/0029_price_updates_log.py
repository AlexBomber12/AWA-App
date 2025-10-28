from __future__ import annotations

from textwrap import dedent

from alembic import op  # type: ignore[attr-defined]

revision = "0029_price_updates_log"
down_revision = "0028_roi_fees_mviews"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        dedent(
            """
            CREATE TABLE IF NOT EXISTS price_updates_log (
                id BIGSERIAL PRIMARY KEY,
                asin VARCHAR(14) NOT NULL,
                old_price NUMERIC(10, 2),
                new_price NUMERIC(10, 2) NOT NULL,
                strategy VARCHAR(32) NOT NULL,
                actor VARCHAR(32) NOT NULL DEFAULT 'repricer',
                context JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE INDEX IF NOT EXISTS ix_price_updates_log_asin
                ON price_updates_log (asin);
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE INDEX IF NOT EXISTS ix_price_updates_log_created_at
                ON price_updates_log (created_at DESC);
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE INDEX IF NOT EXISTS ix_price_updates_log_strategy
                ON price_updates_log (strategy);
            """
        )
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS price_updates_log;")
