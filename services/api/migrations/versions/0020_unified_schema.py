import sqlalchemy as sa

from alembic import op

revision = "0020_unified_schema"
down_revision = "0006_fix_roi_views"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view     CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_roi_full   CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_refund_totals  CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_reimb_totals   CASCADE;")

    op.create_table(
        "returns_raw",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("asin", sa.Text, nullable=False),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("refund_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("return_date", sa.Date, nullable=False),
    )
    op.create_table(
        "reimbursements_raw",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("asin", sa.Text, nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reimb_date", sa.Date, nullable=False),
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW v_refund_totals AS
          SELECT asin, SUM(qty) AS refunds
            FROM returns_raw GROUP BY asin;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW v_reimb_totals AS
          SELECT asin, SUM(amount) AS reimbursements
            FROM reimbursements_raw GROUP BY asin;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW v_roi_full AS
        WITH base AS (
            SELECT
                p.asin,
                vp.cost,
                (f.fulfil_fee + f.referral_fee + f.storage_fee) AS fees,
                COALESCE(rt.refunds,0)         AS refunds,
                COALESCE(rbt.reimbursements,0) AS reimbursements,
                k.buybox_price
            FROM products       p
            JOIN vendor_prices  vp  ON vp.sku  = p.asin
            JOIN fees_raw       f   ON f.asin  = p.asin
            JOIN keepa_offers   k   ON k.asin  = p.asin
            LEFT JOIN v_refund_totals  rt  ON rt.asin  = p.asin
            LEFT JOIN v_reimb_totals   rbt ON rbt.asin = p.asin
        )
        SELECT
            asin,
            cost,
            fees,
            refunds,
            reimbursements,
            buybox_price,
            ROUND(
                100 * ((buybox_price - cost - fees - refunds + reimbursements) / cost),
                1
            ) AS roi_pct
        FROM base;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW roi_view AS
          SELECT asin, roi_pct
            FROM v_roi_full
           WHERE roi_pct < 5;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_roi_full CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_refund_totals CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_reimb_totals CASCADE;")
    op.drop_table("reimbursements_raw")
    op.drop_table("returns_raw")
