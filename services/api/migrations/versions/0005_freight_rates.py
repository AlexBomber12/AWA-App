from textwrap import dedent
from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0005_freight_rates"
down_revision = "0004_fee_cron"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = inspect(bind).get_table_names()
    if "freight_rates" not in tables:
        op.create_table(
            "freight_rates",
            sa.Column("lane", sa.Text(), primary_key=True),
            sa.Column("mode", sa.Text(), primary_key=True),
            sa.Column("eur_per_kg", sa.Numeric(10, 2), nullable=False),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )

    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute("DROP VIEW IF EXISTS v_roi_full")

    op.execute(
        dedent(
            """
            CREATE VIEW roi_view AS
            SELECT
              p.asin,
              (
                SELECT cost FROM vendor_prices vp
                WHERE vp.sku = p.asin
                ORDER BY vp.updated_at DESC
                LIMIT 1
              ) AS cost,
              f.fulfil_fee,
              f.referral_fee,
              f.storage_fee,
              k.buybox_price,
              (
                COALESCE(p.weight_kg, 0)
                * COALESCE((SELECT eur_per_kg FROM freight_rates LIMIT 1), 0)
              ) AS freight_cost,
              ROUND(
                100 * (
                  k.buybox_price
                  - (
                    SELECT cost FROM vendor_prices vp
                    WHERE vp.sku = p.asin
                    ORDER BY vp.updated_at DESC
                    LIMIT 1
                  )
                  - f.fulfil_fee
                  - f.referral_fee
                  - f.storage_fee
                  - (
                        COALESCE(p.weight_kg, 0)
                        * COALESCE((SELECT eur_per_kg FROM freight_rates LIMIT 1), 0)
                    )
                ) / k.buybox_price,
              2) AS roi_pct
            FROM products p
            JOIN keepa_offers k ON k.asin = p.asin
            JOIN fees_raw      f ON f.asin = p.asin;
            """
        )
    )

    op.execute(
        dedent(
            """
            CREATE VIEW v_roi_full AS
            SELECT
              p.asin,
              (
                SELECT cost FROM vendor_prices vp
                WHERE vp.sku = p.asin
                ORDER BY vp.updated_at DESC
                LIMIT 1
              ) AS cost,
              f.fulfil_fee,
              f.referral_fee,
              f.storage_fee,
              k.buybox_price,
              (
                COALESCE(p.weight_kg, 0)
                * COALESCE((SELECT eur_per_kg FROM freight_rates LIMIT 1), 0)
              ) AS freight_cost,
              ROUND(
                100 * (
                  k.buybox_price
                  - (
                    SELECT cost FROM vendor_prices vp
                    WHERE vp.sku = p.asin
                    ORDER BY vp.updated_at DESC
                    LIMIT 1
                  )
                  - f.fulfil_fee
                  - f.referral_fee
                  - f.storage_fee
                  - (
                        COALESCE(p.weight_kg, 0)
                        * COALESCE((SELECT eur_per_kg FROM freight_rates LIMIT 1), 0)
                    )
                ) / k.buybox_price,
              2) AS roi_pct
            FROM products p
            JOIN keepa_offers k  ON k.asin = p.asin
            JOIN fees_raw    f  ON f.asin = p.asin;
            """
        )
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute("DROP VIEW IF EXISTS v_roi_full")
    bind = op.get_bind()
    tables = inspect(bind).get_table_names()
    if "freight_rates" in tables:
        op.drop_table("freight_rates")
    op.execute(
        dedent(
            """
            CREATE VIEW roi_view AS
            SELECT
              p.asin,
              (
                SELECT cost FROM vendor_prices vp
                WHERE vp.sku = p.asin
                ORDER BY vp.updated_at DESC
                LIMIT 1
              ) AS cost,
              f.fulfil_fee,
              f.referral_fee,
              f.storage_fee,
              k.buybox_price,
              ROUND(
                100 * (
                  k.buybox_price
                  - (
                    SELECT cost FROM vendor_prices vp
                    WHERE vp.sku = p.asin
                    ORDER BY vp.updated_at DESC
                    LIMIT 1
                  )
                  - f.fulfil_fee
                  - f.referral_fee
                  - f.storage_fee
                ) / k.buybox_price,
              2) AS roi_pct
            FROM products p
            JOIN keepa_offers k ON k.asin = p.asin
            JOIN fees_raw      f ON f.asin = p.asin;
            """
        )
    )
    op.execute(
        dedent(
            """
            CREATE VIEW v_roi_full AS
            SELECT
              p.asin,
              (
                SELECT cost FROM vendor_prices vp
                WHERE vp.sku = p.asin
                ORDER BY vp.updated_at DESC
                LIMIT 1
              ) AS cost,
              f.fulfil_fee,
              f.referral_fee,
              f.storage_fee,
              k.buybox_price,
              ROUND(
                100 * (
                  k.buybox_price
                  - (
                    SELECT cost FROM vendor_prices vp
                    WHERE vp.sku = p.asin
                    ORDER BY vp.updated_at DESC
                    LIMIT 1
                  )
                  - f.fulfil_fee
                  - f.referral_fee
                  - f.storage_fee
                ) / k.buybox_price,
              2) AS roi_pct
            FROM products p
            JOIN keepa_offers k  ON k.asin = p.asin
            JOIN fees_raw    f  ON f.asin = p.asin;
            """
        )
    )
