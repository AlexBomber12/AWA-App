from alembic import op  # type: ignore[attr-defined]
from textwrap import dedent

revision = "0006_fix_roi_views"
down_revision = "0004_fee_cron"
branch_labels = depends_on = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view CASCADE")
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
               k.buybox_price,
               ROUND(
                 100 * (k.buybox_price - vp.cost - f.fulfil_fee - f.referral_fee - f.storage_fee)
                 / vp.cost , 1) AS roi_pct
        FROM products      p
        JOIN vendor_prices vp ON vp.sku = p.asin
        JOIN fees_raw      f  ON f.asin = p.asin
        JOIN keepa_offers  k  ON k.asin = p.asin;
            """
        )
    )
    op.execute(dedent("CREATE VIEW roi_view AS SELECT asin, roi_pct FROM v_roi_full;"))


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute("DROP VIEW IF EXISTS v_roi_full")
