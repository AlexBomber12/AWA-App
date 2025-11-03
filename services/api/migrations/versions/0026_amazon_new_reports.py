import sqlalchemy as sa
from alembic import op

revision = "0026_amazon_new_reports"
down_revision = "0025_pr4_indexes_loadlog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fee_preview_raw",
        sa.Column("asin", sa.Text(), nullable=False),
        sa.Column("sku", sa.Text(), nullable=True),
        sa.Column("fnsku", sa.Text(), nullable=True),
        sa.Column("referral_fee", sa.Float(), nullable=True),
        sa.Column("fulfillment_fee", sa.Float(), nullable=True),
        sa.Column("storage_fee", sa.Float(), nullable=True),
        sa.Column("estimated_fee_total", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column(
            "captured_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_fee_preview_raw_asin", "fee_preview_raw", ["asin"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS brin_fee_preview_raw_captured_at ON fee_preview_raw USING brin (captured_at)"
    )

    op.create_table(
        "inventory_ledger_raw",
        sa.Column("event_date", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("asin", sa.Text(), nullable=True),
        sa.Column("sku", sa.Text(), nullable=True),
        sa.Column("fnsku", sa.Text(), nullable=True),
        sa.Column("warehouse", sa.Text(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("reference_id", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
    )
    op.create_index("idx_inventory_ledger_raw_asin", "inventory_ledger_raw", ["asin"], unique=False)
    op.execute(
        "CREATE INDEX IF NOT EXISTS brin_inventory_ledger_raw_event_date ON inventory_ledger_raw USING brin (event_date)"
    )

    op.create_table(
        "ads_sp_cost_daily_raw",
        sa.Column("date", sa.DATE(), nullable=False),
        sa.Column("campaign_id", sa.Text(), nullable=False),
        sa.Column("ad_group_id", sa.Text(), nullable=False),
        sa.Column("keyword_id", sa.Text(), nullable=True),
        sa.Column("targeting", sa.Text(), nullable=True),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("spend", sa.Float(), nullable=False),
        sa.Column("orders", sa.Integer(), nullable=True),
        sa.Column("sales", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
    )
    op.create_index(
        "idx_ads_sp_cost_daily_raw_date",
        "ads_sp_cost_daily_raw",
        ["date"],
        unique=False,
    )
    op.create_index(
        "idx_ads_sp_cost_daily_raw_campaign",
        "ads_sp_cost_daily_raw",
        ["campaign_id"],
        unique=False,
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS brin_ads_sp_cost_daily_raw_date ON ads_sp_cost_daily_raw USING brin (date)"
    )
    op.create_index(
        "uq_ads_sp_cost_daily_raw_key",
        "ads_sp_cost_daily_raw",
        ["date", "campaign_id", "ad_group_id", "keyword_id"],
        unique=True,
    )

    op.create_table(
        "settlements_txn_raw",
        sa.Column("settlement_id", sa.Text(), nullable=False),
        sa.Column("posted_date", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("transaction_type", sa.Text(), nullable=False),
        sa.Column("order_id", sa.Text(), nullable=True),
        sa.Column("sku", sa.Text(), nullable=True),
        sa.Column("asin", sa.Text(), nullable=True),
        sa.Column("marketplace", sa.Text(), nullable=True),
        sa.Column("amount_type", sa.Text(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("transaction_id", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_settlements_txn_raw_settlement",
        "settlements_txn_raw",
        ["settlement_id"],
        unique=False,
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS brin_settlements_txn_raw_posted_date ON settlements_txn_raw USING brin (posted_date)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_settlements_txn_raw_transaction_id ON settlements_txn_raw(transaction_id) WHERE transaction_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_settlements_txn_raw_transaction_id")
    op.drop_index(
        "idx_settlements_txn_raw_settlement",
        table_name="settlements_txn_raw",
        if_exists=True,
    )
    op.execute("DROP INDEX IF EXISTS brin_settlements_txn_raw_posted_date")
    op.drop_table("settlements_txn_raw")

    op.drop_index(
        "uq_ads_sp_cost_daily_raw_key",
        table_name="ads_sp_cost_daily_raw",
        if_exists=True,
    )
    op.drop_index(
        "idx_ads_sp_cost_daily_raw_campaign",
        table_name="ads_sp_cost_daily_raw",
        if_exists=True,
    )
    op.drop_index(
        "idx_ads_sp_cost_daily_raw_date",
        table_name="ads_sp_cost_daily_raw",
        if_exists=True,
    )
    op.execute("DROP INDEX IF EXISTS brin_ads_sp_cost_daily_raw_date")
    op.drop_table("ads_sp_cost_daily_raw")

    op.execute("DROP INDEX IF EXISTS brin_inventory_ledger_raw_event_date")
    op.drop_index(
        "idx_inventory_ledger_raw_asin",
        table_name="inventory_ledger_raw",
        if_exists=True,
    )
    op.drop_table("inventory_ledger_raw")

    op.execute("DROP INDEX IF EXISTS brin_fee_preview_raw_captured_at")
    op.drop_index("idx_fee_preview_raw_asin", table_name="fee_preview_raw", if_exists=True)
    op.drop_table("fee_preview_raw")
