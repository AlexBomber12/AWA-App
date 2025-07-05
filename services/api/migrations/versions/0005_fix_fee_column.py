from alembic import op
import sqlalchemy as sa

revision = "0005_fix_fee_column"
down_revision = "0004_fee_cron"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # rename fulf_fee column to fulfil_fee
    with op.batch_alter_table("fees_raw") as batch:
        batch.alter_column(
            "fulf_fee",
            new_column_name="fulfil_fee",
            existing_type=sa.Numeric(),
        )

    # rebuild roi_view with correct column name
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
    with op.batch_alter_table("fees_raw") as batch:
        batch.alter_column(
            "fulfil_fee",
            new_column_name="fulf_fee",
            existing_type=sa.Numeric(),
        )
    op.execute(
        """
        CREATE VIEW roi_view AS
        SELECT
          p.asin,
          vp.cost,
          f.fulf_fee,
          f.referral_fee,
          f.storage_fee,
          k.buybox_price,
          ROUND(
            100 * (
              k.buybox_price
            - vp.cost
            - f.fulf_fee
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
