from textwrap import dedent
from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa

revision = "0012_returns_reimbursements"
down_revision = "0011_load_log_table"
branch_labels = depends_on = None


def upgrade() -> None:
    op.create_table(
        "returns_raw",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("asin", sa.Text(), nullable=False),
        sa.Column("order_id", sa.Text()),
        sa.Column("return_reason", sa.Text()),
        sa.Column("return_date", sa.Date(), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.CheckConstraint("qty>0", name="ck_returns_qty_pos"),
        sa.Column("refund_amount", sa.Numeric(), nullable=False),
        sa.Column("currency", sa.Text()),
        sa.Column(
            "inserted_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "reimbursements_raw",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("asin", sa.Text(), nullable=False),
        sa.Column("reimb_id", sa.Text()),
        sa.Column("reimb_date", sa.Date(), nullable=False),
        sa.Column("qty", sa.Integer()),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("currency", sa.Text()),
        sa.Column("reason_code", sa.Text()),
        sa.Column(
            "inserted_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    op.execute(
        dedent(
            """
            CREATE MATERIALIZED VIEW v_refund_totals AS
            SELECT asin,
                   sum(refund_amount) AS refunds,
                   sum(qty)           AS refund_qty
            FROM returns_raw
            GROUP BY asin;
            """
        )
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_v_refund_totals_pk ON v_refund_totals (asin)")

    op.execute(
        dedent(
            """
            CREATE MATERIALIZED VIEW v_reimb_totals AS
            SELECT asin,
                   sum(amount) AS reimbursements
            FROM reimbursements_raw
            GROUP BY asin;
            """
        )
    )

    op.execute("REFRESH MATERIALIZED VIEW v_refund_totals;")
    op.execute("REFRESH MATERIALIZED VIEW v_reimb_totals;")

    op.execute("DROP VIEW IF EXISTS v_roi_full CASCADE")
    op.execute(
        dedent(
            """
            CREATE VIEW v_roi_full AS
            SELECT p.asin,
                   vp.cost,
                   f.fulfil_fee,
                   f.referral_fee,
                   f.storage_fee,
                   COALESCE(rt.refunds, 0)         AS refunds,
                   COALESCE(rbt.reimbursements, 0) AS reimbursements,
                   k.buybox_price,
                   ROUND(
                     100 * (
                       k.buybox_price
                       - vp.cost
                       - f.fulfil_fee
                       - f.referral_fee
                       - f.storage_fee
                       - COALESCE(rt.refunds,0)/GREATEST(rt.refund_qty,1)
                       + COALESCE(rbt.reimbursements,0)/GREATEST(rt.refund_qty,1)
                     ) / vp.cost,
                   1) AS roi_pct
            FROM products p
            JOIN vendor_prices vp ON vp.sku = p.asin
            JOIN fees_raw      f  ON f.asin = p.asin
            JOIN keepa_offers  k  ON k.asin = p.asin
            LEFT JOIN v_refund_totals rt ON rt.asin = p.asin
            LEFT JOIN v_reimb_totals rbt ON rbt.asin = p.asin;
            """
        )
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_roi_full")
    op.execute("DROP INDEX IF EXISTS idx_v_refund_totals_pk")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS v_reimb_totals")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS v_refund_totals")
    op.drop_table("reimbursements_raw")
    op.drop_table("returns_raw")
