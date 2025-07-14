from alembic import op

revision = "0010_rename_fees_raw"
down_revision = "0009_fees_raw_fix"


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
