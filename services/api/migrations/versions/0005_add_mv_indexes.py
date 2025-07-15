from textwrap import dedent
import os
from alembic import op  # type: ignore[attr-defined]

revision = "0005_add_mv_indexes"
down_revision = "0012_returns_reimbursements"
branch_labels = depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS "
        "ix_v_reimb_totals_pk ON v_reimb_totals (asin)"
    )
    op.execute(
        "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS "
        "ix_v_refund_totals_pk ON v_refund_totals (asin)"
    )

    live = os.getenv("ENABLE_LIVE", "1") != "0"
    option = " CONCURRENTLY" if live else ""
    op.execute(f"REFRESH MATERIALIZED VIEW{option} v_refund_totals")
    op.execute(f"REFRESH MATERIALIZED VIEW{option} v_reimb_totals")

    # create roi_view and v_roi_full if missing
    op.execute(
        dedent(
            """
            CREATE VIEW IF NOT EXISTS v_roi_full AS
            SELECT p.asin,
                   vp.cost,
                   f.fulfil_fee,
                   f.referral_fee,
                   f.storage_fee,
                   fr.eur_per_kg * COALESCE(p.weight_kg, 0) AS freight,
                   k.buybox_price,
                   ROUND(
                     100 * (
                       k.buybox_price
                       - vp.cost
                       - f.fulfil_fee
                       - f.referral_fee
                       - f.storage_fee
                       - fr.eur_per_kg * COALESCE(p.weight_kg, 0)
                     ) / vp.cost,
                   1) AS roi_pct
            FROM products p
            JOIN vendor_prices vp ON vp.sku = p.asin
            JOIN fees_raw      f  ON f.asin = p.asin
            JOIN freight_rates fr ON fr.lane='EU→IT' AND fr.mode='sea'
            JOIN keepa_offers  k  ON k.asin = p.asin;
            """
        )
    )
    op.execute("CREATE VIEW IF NOT EXISTS roi_view AS SELECT asin, roi_pct FROM v_roi_full")


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute("DROP VIEW IF EXISTS v_roi_full")
    op.execute("DROP INDEX IF EXISTS ix_v_refund_totals_pk")
    op.execute("DROP INDEX IF EXISTS ix_v_reimb_totals_pk")
