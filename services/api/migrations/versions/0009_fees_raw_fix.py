from alembic import op  # type: ignore[attr-defined]

revision = "0009_fees_raw_fix"
down_revision = "0006_fix_roi_views"
branch_labels = depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS fees_raw CASCADE")
    op.execute(
        "CREATE TABLE fees_raw("
        "sku text primary key, fee numeric, captured_at timestamptz default now())"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS fees_raw")
