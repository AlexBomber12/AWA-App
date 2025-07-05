from textwrap import dedent
from alembic import op
import sqlalchemy as sa

revision = "0003_vendor_prices"
down_revision = "0002_create_roi_view"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), unique=True, nullable=False),
    )
    op.create_table(
        "vendor_prices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id")),
        sa.Column("sku", sa.Text(), nullable=False),
        sa.Column("cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("moq", sa.Integer(), server_default="0"),
        sa.Column("lead_time_days", sa.Integer(), server_default="0"),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")
        ),
        sa.UniqueConstraint("vendor_id", "sku", name="u_vendor_sku"),
    )
    op.create_table(
        "keepa_offers",
        sa.Column("asin", sa.Text(), primary_key=True),
        sa.Column("buybox_price", sa.Numeric(10, 2)),
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


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_roi_full")
    op.drop_table("keepa_offers")
    op.drop_table("vendor_prices")
    op.drop_table("vendors")
