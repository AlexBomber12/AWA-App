from __future__ import annotations

from textwrap import dedent

from alembic import op
from services.db.utils.views import replace_view

revision = "0026_fix_refund_views"
down_revision = "0025_pr4_indexes_loadlog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_roi_full CASCADE")
    op.execute("DROP VIEW IF EXISTS v_refund_totals CASCADE")
    op.execute("DROP VIEW IF EXISTS v_reimb_totals CASCADE")
    op.execute("DROP VIEW IF EXISTS v_refunds_summary CASCADE")
    op.execute("DROP VIEW IF EXISTS v_refunds_txn CASCADE")

    replace_view(
        "v_refunds_txn",
        dedent(
            """
            CREATE VIEW v_refunds_txn AS
            SELECT
                asin,
                NULL::text AS order_id,
                refund_amount AS refund_amount,
                'USD'::text AS currency,
                return_date::timestamp AS refunded_at,
                'return'::text AS source
            FROM returns_raw
            UNION ALL
            SELECT
                asin,
                NULL::text AS order_id,
                -amount AS refund_amount,
                'USD'::text AS currency,
                reimb_date::timestamp AS refunded_at,
                'reimbursement'::text AS source
            FROM reimbursements_raw;
            """
        ),
    )

    replace_view(
        "v_refunds_summary",
        dedent(
            """
            CREATE VIEW v_refunds_summary AS
            SELECT
                asin,
                DATE(refunded_at) AS date,
                SUM(refund_amount) AS refund_amount
            FROM v_refunds_txn
            GROUP BY asin, DATE(refunded_at);
            """
        ),
    )

    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW v_roi_full AS
            SELECT
              p.asin,
              vp.cost,
              f.fulfil_fee,
              f.referral_fee,
              COALESCE(f.storage_fee, 0) AS storage_fee,
              k.buybox_price,
              ROUND(
                100 * (
                  k.buybox_price
                  - (f.fulfil_fee + f.referral_fee + COALESCE(f.storage_fee, 0))
                  - vp.cost
                  - COALESCE(rf.refunds, 0)
                ) / NULLIF(vp.cost, 0),
                1
              ) AS roi_pct
            FROM products p
            JOIN (
              SELECT v1.*
              FROM vendor_prices v1
              JOIN (
                SELECT sku, MAX(updated_at) AS max_ts
                FROM vendor_prices
                GROUP BY sku
              ) v2 ON v2.sku = v1.sku AND v2.max_ts = v1.updated_at
            ) vp ON vp.sku = p.asin
            JOIN fees_raw f ON f.asin = p.asin
            JOIN keepa_offers k ON k.asin = p.asin
            LEFT JOIN (
                SELECT asin, SUM(refund_amount) AS refunds
                FROM v_refunds_txn
                GROUP BY asin
            ) rf ON rf.asin = p.asin;
            """
        )
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_roi_full CASCADE")
    op.execute("DROP VIEW IF EXISTS v_refunds_summary CASCADE")
    op.execute("DROP VIEW IF EXISTS v_refunds_txn CASCADE")

    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW v_refund_totals AS
              SELECT asin, SUM(qty) AS refunds
                FROM returns_raw GROUP BY asin;
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW v_reimb_totals AS
              SELECT asin, SUM(amount) AS reimbursements
                FROM reimbursements_raw GROUP BY asin;
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW v_roi_full AS
            SELECT
              p.asin,
              vp.cost,
              f.fulfil_fee,
              f.referral_fee,
              COALESCE(f.storage_fee, 0) AS storage_fee,
              k.buybox_price,
              ROUND(
                100 * (
                  k.buybox_price
                  - (f.fulfil_fee + f.referral_fee + COALESCE(f.storage_fee, 0))
                  - vp.cost
                  - COALESCE(rt.refunds, 0)
                  + COALESCE(rbt.reimbursements, 0)
                ) / NULLIF(vp.cost, 0),
                1
              ) AS roi_pct
            FROM products p
            JOIN (
              SELECT v1.*
              FROM vendor_prices v1
              JOIN (
                SELECT sku, MAX(updated_at) AS max_ts
                FROM vendor_prices
                GROUP BY sku
              ) v2 ON v2.sku = v1.sku AND v2.max_ts = v1.updated_at
            ) vp ON vp.sku = p.asin
            JOIN fees_raw f ON f.asin = p.asin
            JOIN keepa_offers k ON k.asin = p.asin
            LEFT JOIN v_refund_totals rt ON rt.asin = p.asin
            LEFT JOIN v_reimb_totals rbt ON rbt.asin = p.asin;
            """
        )
    )
