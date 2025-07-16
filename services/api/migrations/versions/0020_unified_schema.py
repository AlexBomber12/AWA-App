from alembic import op
import sqlalchemy as sa

revision = "0020_unified_schema"
down_revision = "0006_fix_roi_views"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1/ returns + reimburse
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
    # 2/ materialised views + unique indexes
    op.execute(
        """
      CREATE MATERIALIZED VIEW IF NOT EXISTS v_refund_totals AS
      SELECT asin, SUM(refund_amount)::numeric AS refunds
        FROM returns_raw GROUP BY asin
    """
    )
    op.execute(
        """
      CREATE MATERIALIZED VIEW IF NOT EXISTS v_reimb_totals AS
      SELECT asin, SUM(amount)::numeric AS reimbursements
        FROM reimbursements_raw GROUP BY asin
    """
    )
    op.execute(
        """
      CREATE UNIQUE INDEX IF NOT EXISTS ux_v_refund_totals
        ON v_refund_totals (asin);
      CREATE UNIQUE INDEX IF NOT EXISTS ux_v_reimb_totals
        ON v_reimb_totals  (asin);
    """
    )
    # 3/ roi_view & v_roi_full
    op.execute(
        """
      CREATE OR REPLACE VIEW v_roi_full AS
      SELECT p.asin,
             vp.cost,
             f.fulfil_fee + f.referral_fee + f.storage_fee          AS fees,
             COALESCE(rt.refunds,0)                                 AS refunds,
             COALESCE(rbt.reimbursements,0)                         AS reimbursements,
             k.buybox_price,
             ROUND( 100 *
                ( k.buybox_price
                  - vp.cost
                  - fees
                  - COALESCE(rt.refunds,0)
                  + COALESCE(rbt.reimbursements,0)
                ) / vp.cost , 1)                                    AS roi_pct
        FROM products        p
        JOIN vendor_prices   vp  ON vp.sku  = p.asin
        JOIN fees_raw        f   ON f.asin  = p.asin
        JOIN keepa_offers    k   ON k.asin  = p.asin
   LEFT JOIN v_refund_totals rt  USING (asin)
   LEFT JOIN v_reimb_totals  rbt USING (asin);
    """
    )
    op.execute("CREATE OR REPLACE VIEW roi_view AS SELECT asin, roi_pct FROM v_roi_full;")


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute("DROP VIEW IF EXISTS v_roi_full")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS v_reimb_totals")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS v_refund_totals")
    op.drop_table("reimbursements_raw")
    op.drop_table("returns_raw")
