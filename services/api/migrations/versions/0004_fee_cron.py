from alembic import op
import sqlalchemy as sa

revision = "0004_fee_cron"
down_revision = "0003_vendor_prices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # extend fees_raw in-place
    with op.batch_alter_table("fees_raw") as t:
        t.add_column(
            sa.Column(
                "storage_fee", sa.Numeric(10, 2), nullable=False, server_default="0"
            )
        )
        t.add_column(
            sa.Column("currency", sa.CHAR(3), nullable=False, server_default="€")
        )
        t.add_column(
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            )
        )
    op.execute("ALTER TABLE fees_raw ALTER COLUMN storage_fee DROP DEFAULT")

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
    with op.batch_alter_table("fees_raw") as t:
        t.drop_column("updated_at")
        t.drop_column("currency")
        t.drop_column("storage_fee")
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
