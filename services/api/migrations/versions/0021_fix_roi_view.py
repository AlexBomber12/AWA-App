"""Fix ROI views to use numeric refunds"""

from sqlalchemy import text

from alembic import context, op

revision = "0022_fix_roi_view"
down_revision = "0020_unified_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if context.is_offline_mode():
        return
    with op.get_context().autocommit_block():
        op.execute(text("DROP VIEW IF EXISTS roi_view CASCADE"))
        op.execute(text("DROP VIEW IF EXISTS v_roi_full CASCADE"))
        op.execute(text("DROP VIEW IF EXISTS v_refund_totals CASCADE"))
        op.execute(text("DROP VIEW IF EXISTS v_reimb_totals CASCADE"))
        op.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS refunds_raw (
                    asin TEXT PRIMARY KEY,
                    amount NUMERIC,
                    created_at TIMESTAMP
                );
                """
            )
        )
        op.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS reimb_raw (
                    asin TEXT PRIMARY KEY,
                    amount NUMERIC,
                    created_at TIMESTAMP
                );
                """
            )
        )
        op.execute(
            text(
                """
                CREATE VIEW v_refund_totals AS
                  SELECT asin, SUM(amount::numeric) AS refunds
                    FROM refunds_raw GROUP BY asin;
                """
            )
        )
        op.execute(
            text(
                """
                CREATE VIEW v_reimb_totals AS
                  SELECT asin, SUM(amount) AS reimbursements
                    FROM reimb_raw GROUP BY asin;
                """
            )
        )
        op.execute(
            text(
                """
                CREATE VIEW v_roi_full AS
                SELECT
                    p.asin,
                    vp.cost,
                    f.fulfil_fee + f.referral_fee + f.storage_fee AS fees,
                    COALESCE(rt.refunds, 0) AS refunds,
                    COALESCE(rbt.reimbursements, 0) AS reimbursements,
                    k.buybox_price,
                    ROUND(
                        100 * (
                            k.buybox_price
                            - vp.cost
                            - (f.fulfil_fee + f.referral_fee + f.storage_fee)
                            - COALESCE(rt.refunds, 0)
                            + COALESCE(rbt.reimbursements, 0)
                        ) / vp.cost,
                        1
                    ) AS roi_pct
                FROM products AS p
                JOIN vendor_prices AS vp ON vp.sku = p.asin
                JOIN fees_raw AS f ON f.asin = p.asin
                JOIN keepa_offers AS k ON k.asin = p.asin
                LEFT JOIN v_refund_totals AS rt ON rt.asin = p.asin
                LEFT JOIN v_reimb_totals AS rbt ON rbt.asin = p.asin;
                """
            )
        )
        op.execute(
            text(
                """
                CREATE VIEW roi_view AS
                  SELECT asin, roi_pct FROM v_roi_full;
                """
            )
        )


def downgrade() -> None:
    if context.is_offline_mode():
        return
    with op.get_context().autocommit_block():
        op.execute(text("DROP VIEW IF EXISTS roi_view CASCADE"))
        op.execute(text("DROP VIEW IF EXISTS v_roi_full CASCADE"))
        op.execute(text("DROP VIEW IF EXISTS v_reimb_totals CASCADE"))
        op.execute(text("DROP VIEW IF EXISTS v_refund_totals CASCADE"))
        op.execute(text("DROP TABLE IF EXISTS reimb_raw"))
        op.execute(text("DROP TABLE IF EXISTS refunds_raw"))
        op.execute(
            text(
                """
                CREATE VIEW v_refund_totals AS
                  SELECT asin, SUM(qty) AS refunds
                    FROM returns_raw GROUP BY asin;
                """
            )
        )
        op.execute(
            text(
                """
                CREATE VIEW v_reimb_totals AS
                  SELECT asin, SUM(amount) AS reimbursements
                    FROM reimbursements_raw GROUP BY asin;
                """
            )
        )
        op.execute(
            text(
                """
                CREATE VIEW v_roi_full AS
                WITH base AS (
                    SELECT
                        p.asin,
                        vp.cost,
                        (f.fulfil_fee + f.referral_fee + f.storage_fee) AS fees,
                        COALESCE(rt.refunds,0) AS refunds,
                        COALESCE(rbt.reimbursements,0) AS reimbursements,
                        k.buybox_price
                    FROM products p
                    JOIN vendor_prices vp ON vp.sku = p.asin
                    JOIN fees_raw f ON f.asin = p.asin
                    JOIN keepa_offers k ON k.asin = p.asin
                    LEFT JOIN v_refund_totals rt ON rt.asin = p.asin
                    LEFT JOIN v_reimb_totals rbt ON rbt.asin = p.asin
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
        )
        op.execute(
            text(
                """
                CREATE VIEW roi_view AS
                  SELECT asin, roi_pct
                    FROM v_roi_full
                   WHERE roi_pct < 5;
                """
            )
        )
