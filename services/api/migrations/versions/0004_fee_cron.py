from alembic import op

revision = "0004_fee_cron"
down_revision = "0003_vendor_prices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # extend fees_raw safely
    op.execute(
        """
        ALTER TABLE fees_raw
            ADD COLUMN IF NOT EXISTS storage_fee NUMERIC(10,2) NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS currency     CHAR(3)      NOT NULL DEFAULT '€',
            ADD COLUMN IF NOT EXISTS updated_at   TIMESTAMPTZ  NOT NULL DEFAULT now();
        """
    )

    # replace roi_view (now includes storage_fee)
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute(
        """
    CREATE VIEW roi_view AS
    SELECT
      p.asin,
      vp.cost,
      f.fulfil_fee,
      f.referral_fee,
      f.storage_fee,
      k.buybox_price,
      ROUND(
        100 * (
          k.buybox_price
        - vp.cost
        - f.fulfil_fee
        - f.referral_fee
        - f.storage_fee
        ) / k.buybox_price, 2
      ) AS roi_pct
    FROM products p
    JOIN keepa_offers k ON k.asin = p.asin
    JOIN fees_raw      f ON f.asin = p.asin
    JOIN LATERAL (
      SELECT cost
      FROM vendor_prices vp
      WHERE vp.sku = p.asin
      ORDER BY vp.updated_at DESC
      LIMIT 1
    ) vp ON TRUE;
    """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute(
        """
        ALTER TABLE fees_raw
            DROP COLUMN IF EXISTS updated_at,
            DROP COLUMN IF EXISTS currency,
            DROP COLUMN IF EXISTS storage_fee;
        """
    )
    op.execute(
        """
    CREATE VIEW roi_view AS
    SELECT
      p.asin,
      vp.cost,
      f.fulfil_fee,
      f.referral_fee,
      k.buybox_price,
      ROUND(
        100 * (
          k.buybox_price
        - vp.cost
        - f.fulfil_fee
        - f.referral_fee
        ) / k.buybox_price, 2
      ) AS roi_pct
    FROM products p
    JOIN keepa_offers k ON k.asin = p.asin
    JOIN fees_raw      f ON f.asin = p.asin
    JOIN LATERAL (
      SELECT cost
      FROM vendor_prices vp
      WHERE vp.sku = p.asin
      ORDER BY vp.updated_at DESC
      LIMIT 1
    ) vp ON TRUE;
    """
    )
