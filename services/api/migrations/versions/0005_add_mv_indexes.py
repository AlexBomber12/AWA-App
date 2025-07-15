from __future__ import annotations

import os
from textwrap import dedent

from alembic import op  # type: ignore[attr-defined]

revision = "0005_add_mv_indexes"
down_revision = "0012_returns_reimbursements"
branch_labels = depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS"
        " ix_v_reimb_totals_pk ON v_reimb_totals (asin)"
    )
    op.execute(
        "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS"
        " ix_v_refund_totals_pk ON v_refund_totals (asin)"
    )

    op.execute(
        dedent(
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS v_reimb_totals AS
            SELECT asin, sum(amount) AS reimbursements
            FROM reimbursements_raw
            GROUP BY asin;
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS v_refund_totals AS
            SELECT asin, sum(refund_amount) AS refunds, sum(qty) AS refund_qty
            FROM returns_raw
            GROUP BY asin;
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE VIEW IF NOT EXISTS v_roi_full AS
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
    op.execute("CREATE VIEW IF NOT EXISTS roi_view AS SELECT asin, roi_pct FROM v_roi_full")
    concurrent = " CONCURRENTLY" if os.getenv("ENABLE_LIVE", "0") != "0" else ""
    op.execute(f"REFRESH MATERIALIZED VIEW{concurrent} v_refund_totals")
    op.execute(f"REFRESH MATERIALIZED VIEW{concurrent} v_reimb_totals")


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute("DROP VIEW IF EXISTS v_roi_full")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS v_refund_totals")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS v_reimb_totals")
    op.execute("DROP INDEX IF EXISTS ix_v_refund_totals_pk")
    op.execute("DROP INDEX IF EXISTS ix_v_reimb_totals_pk")
