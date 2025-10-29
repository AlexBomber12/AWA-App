import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0025_pr4_indexes_loadlog"
down_revision = "0024_create_buybox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "load_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("source_uri", sa.Text(), nullable=False),
        sa.Column("target_table", sa.Text(), nullable=False),
        sa.Column("dialect", sa.Text(), nullable=True),
        sa.Column("file_hash", sa.Text(), nullable=False),
        sa.Column("rows", sa.Integer(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("idx_load_log_started_at", "load_log", ["started_at"], unique=False)
    op.create_index(
        "idx_load_log_table_hash",
        "load_log",
        ["target_table", "file_hash"],
        unique=False,
    )

    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name='reimbursements_raw' AND column_name='reimb_id'
            ) AND NOT EXISTS (
                SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='uq_reimbursements_raw_reimb_id'
            ) THEN
                CREATE UNIQUE INDEX uq_reimbursements_raw_reimb_id ON reimbursements_raw(reimb_id);
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='uq_reimbursements_raw_reimb_id'
            ) AND NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname='reimbursements_raw_pkey'
            ) THEN
                ALTER TABLE reimbursements_raw ADD CONSTRAINT reimbursements_raw_pkey PRIMARY KEY USING INDEX uq_reimbursements_raw_reimb_id;
            END IF;
        END $$;
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS idx_returns_raw_asin ON returns_raw(asin);")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name='returns_raw' AND column_name='return_date'
            ) THEN
                CREATE INDEX IF NOT EXISTS brin_returns_raw_return_date ON returns_raw USING brin (return_date);
            ELSIF EXISTS (
                SELECT 1 FROM information_schema.columns WHERE table_name='returns_raw' AND column_name='processed_at'
            ) THEN
                CREATE INDEX IF NOT EXISTS brin_returns_raw_processed_at ON returns_raw USING brin (processed_at);
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS brin_returns_raw_return_date")
    op.execute("DROP INDEX IF EXISTS brin_returns_raw_processed_at")
    op.execute("DROP INDEX IF EXISTS idx_returns_raw_asin")
    op.execute(
        "ALTER TABLE reimbursements_raw DROP CONSTRAINT IF EXISTS reimbursements_raw_pkey"
    )
    op.execute("DROP INDEX IF EXISTS uq_reimbursements_raw_reimb_id")
    op.drop_index("idx_load_log_table_hash", table_name="load_log", if_exists=True)
    op.drop_index("idx_load_log_started_at", table_name="load_log", if_exists=True)
    op.drop_table("load_log")
