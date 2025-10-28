from __future__ import annotations

from textwrap import dedent

from alembic import op  # type: ignore[attr-defined]

revision = "0028_roi_fees_mviews"
down_revision = "0027_merge_reports_refund_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_roi_full CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mat_v_roi_full CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mat_fees_expanded CASCADE;")

    op.execute(
        dedent(
            """
            CREATE MATERIALIZED VIEW mat_v_roi_full AS
            WITH ranked_vendor_prices AS (
                SELECT v1.*
                FROM vendor_prices v1
                JOIN (
                    SELECT sku, MAX(updated_at) AS max_ts
                    FROM vendor_prices
                    GROUP BY sku
                ) v2 ON v2.sku = v1.sku AND v2.max_ts = v1.updated_at
            ),
            refund_rollup AS (
                SELECT
                    asin,
                    SUM(CASE WHEN refund_amount > 0 THEN refund_amount ELSE 0 END) AS refunds,
                    SUM(CASE WHEN refund_amount < 0 THEN -refund_amount ELSE 0 END) AS reimbursements
                FROM v_refunds_txn
                GROUP BY asin
            ),
            latest_fees AS (
                SELECT DISTINCT ON (asin)
                    asin,
                    COALESCE(fulfil_fee, 0) AS fulfil_fee,
                    COALESCE(referral_fee, 0) AS referral_fee,
                    COALESCE(storage_fee, 0) AS storage_fee
                FROM fees_raw
                ORDER BY asin, COALESCE(updated_at, captured_at, CURRENT_TIMESTAMP) DESC, captured_at DESC
            )
            SELECT
                p.asin,
                vp.cost,
                lf.fulfil_fee,
                lf.referral_fee,
                lf.storage_fee,
                (lf.fulfil_fee + lf.referral_fee + lf.storage_fee) AS fees,
                k.buybox_price,
                ROUND(
                    100 * (
                        k.buybox_price
                        - (lf.fulfil_fee + lf.referral_fee + lf.storage_fee)
                        - vp.cost
                        - COALESCE(rr.refunds, 0)
                        + COALESCE(rr.reimbursements, 0)
                    ) / NULLIF(vp.cost, 0),
                    1
                ) AS roi_pct,
                COALESCE(rr.refunds, 0) AS refunds,
                COALESCE(rr.reimbursements, 0) AS reimbursements
            FROM products p
            JOIN ranked_vendor_prices vp ON vp.sku = p.asin
            JOIN latest_fees lf ON lf.asin = p.asin
            JOIN keepa_offers k ON k.asin = p.asin
            LEFT JOIN refund_rollup rr ON rr.asin = p.asin;
            """
        )
    )

    op.execute(
        dedent(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ix_mat_v_roi_full_pk
                ON mat_v_roi_full (asin);
            """
        )
    )

    op.execute(
        dedent(
            """
            CREATE MATERIALIZED VIEW mat_fees_expanded AS
            WITH latest_fees AS (
                SELECT DISTINCT ON (asin)
                    asin,
                    COALESCE(fulfil_fee, 0) AS fulfil_fee,
                    COALESCE(referral_fee, 0) AS referral_fee,
                    COALESCE(storage_fee, 0) AS storage_fee
                FROM fees_raw
                ORDER BY asin, COALESCE(updated_at, captured_at, CURRENT_TIMESTAMP) DESC, captured_at DESC
            )
            SELECT
                asin,
                fulfil_fee,
                referral_fee,
                storage_fee,
                fulfil_fee + referral_fee + storage_fee AS fees
            FROM latest_fees;
            """
        )
    )

    op.execute(
        dedent(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ix_mat_fees_expanded_pk
                ON mat_fees_expanded (asin);
            """
        )
    )

    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW v_roi_full AS
            SELECT * FROM mat_v_roi_full;
            """
        )
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_roi_full CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mat_v_roi_full CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mat_fees_expanded CASCADE;")

    op.execute("DROP VIEW IF EXISTS v_refund_totals CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_reimb_totals CASCADE;")

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
