"""Fix v_roi_full ambiguous asin join

Revision ID: 0021_fix_roi_view
Revises: 0020_unified_schema
Create Date: 2025-07-16
"""

from alembic import op

revision: str = "0021_fix_roi_view"
down_revision: str = "0020_unified_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DROP VIEW IF EXISTS v_roi_full;
        CREATE VIEW v_roi_full AS
        SELECT
            p.asin,
            vp.cost,
            f.fulfil_fee + f.referral_fee + f.storage_fee        AS fees,
            COALESCE(rt.refunds, 0)                              AS refunds,
            COALESCE(rbt.reimbursements, 0)                      AS reimbursements,
            k.buybox_price,
            ROUND(
                100 *
                (
                    k.buybox_price
                  - vp.cost
                  - (f.fulfil_fee + f.referral_fee + f.storage_fee)
                  - COALESCE(rt.refunds, 0)
                  + COALESCE(rbt.reimbursements, 0)
                ) / vp.cost,
            1)                                                  AS roi_pct
        FROM products        AS p
        JOIN vendor_prices   AS vp  ON vp.sku  = p.asin
        JOIN fees_raw        AS f   ON f.asin  = p.asin
        JOIN keepa_offers    AS k   ON k.asin  = p.asin
        LEFT JOIN v_refund_totals  AS rt  ON rt.asin  = p.asin
        LEFT JOIN v_reimb_totals   AS rbt ON rbt.asin = p.asin;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_roi_full;")
