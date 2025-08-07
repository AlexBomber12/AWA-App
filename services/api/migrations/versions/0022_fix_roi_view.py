from textwrap import dedent

from alembic import op  # type: ignore[attr-defined]


revision = "0022_fix_roi_view"
down_revision = "0020_unified_schema"
branch_labels = None
depends_on = None


VIEW_SQL = """
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
    ) / NULLIF(vp.cost, 0)
  , 1) AS roi_pct
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


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_roi_full CASCADE")
    op.execute(dedent(VIEW_SQL))
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_asin ON products(asin)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_fees_raw_asin ON fees_raw(asin)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_keepa_offers_asin ON keepa_offers(asin)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vendor_prices_sku_updated_at ON vendor_prices (sku, updated_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_vendor_prices_sku_updated_at")
    op.execute("DROP INDEX IF EXISTS ix_keepa_offers_asin")
    op.execute("DROP INDEX IF EXISTS ix_fees_raw_asin")
    op.execute("DROP INDEX IF EXISTS ix_products_asin")
    op.execute("DROP VIEW IF EXISTS v_roi_full CASCADE")

