from alembic import op

revision, down_revision = "0009_fees_raw_fix", "0009_fees_raw_fix"


def upgrade():
    op.execute("DROP TABLE IF EXISTS fees_raw CASCADE")
    op.execute(
        """
        CREATE TABLE fees_raw(
          asin text primary key,
          fee numeric,
          captured_at timestamptz default now()
        )
        """
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS fees_raw")
