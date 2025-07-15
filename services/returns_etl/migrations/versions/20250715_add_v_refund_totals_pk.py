from alembic import op  # type: ignore[attr-defined]

revision = "20250715_add_v_refund_totals_pk"
down_revision = None
branch_labels = depends_on = None


def upgrade() -> None:
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_v_refund_totals_pk ON v_refund_totals (asin)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_v_refund_totals_pk")
