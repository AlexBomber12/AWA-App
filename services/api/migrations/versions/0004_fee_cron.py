from textwrap import dedent
from alembic import op  # type: ignore
import sqlalchemy as sa

revision = "0004_fee_cron"
down_revision = "0003_vendor_prices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_roi_full")
    op.drop_table("fees_raw")
    op.create_table(
        "fees_raw",
        sa.Column("asin", sa.Text(), primary_key=True),
        sa.Column("fulfil_fee", sa.Numeric(10, 2), nullable=False),
        sa.Column("referral_fee", sa.Numeric(10, 2), nullable=False),
        sa.Column("storage_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="€"),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW v_roi_full AS
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


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_roi_full")
    op.drop_table("fees_raw")
    op.create_table(
        "fees_raw",
        sa.Column("asin", sa.TEXT(), primary_key=True),
        sa.Column("fulf_fee", sa.Numeric()),
        sa.Column("referral_fee", sa.Numeric()),
        sa.Column("storage_fee", sa.Numeric()),
        sa.Column("captured_at", sa.TIMESTAMP(timezone=True)),
    )
    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW v_roi_full AS
            SELECT
              p.asin,
              (
                SELECT cost FROM vendor_prices vp
                WHERE vp.sku = p.asin
                ORDER BY vp.updated_at DESC
                LIMIT 1
              ) AS cost,
              f.fulf_fee,
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
                  - f.fulf_fee
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
