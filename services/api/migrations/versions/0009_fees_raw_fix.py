from alembic import op  # type: ignore[attr-defined]

revision = "0009_fees_raw_fix"
down_revision = "0008_load_log"
branch_labels = depends_on = None


def upgrade() -> None:
    # Deprecated; no changes required.
    pass


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS fees_raw")
