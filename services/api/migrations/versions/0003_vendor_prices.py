from textwrap import dedent

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op  # type: ignore[attr-defined]

revision = "0003_vendor_prices"
down_revision = "3e9d5c5aff2c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = inspect(bind).get_table_names()
    if "vendors" not in tables:
        op.create_table(
            "vendors",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.Text(), unique=True, nullable=False),
            sa.Column("locale", sa.Text(), server_default="en"),
            sa.Column("email", sa.Text()),
        )
    if "vendor_prices" not in tables:
        op.create_table(
            "vendor_prices",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id")),
            sa.Column("sku", sa.Text(), nullable=False),
            sa.Column("cost", sa.Numeric(10, 2), nullable=False),
            sa.Column("moq", sa.Integer(), server_default="0"),
            sa.Column("lead_time_days", sa.Integer(), server_default="0"),
            sa.Column("currency", sa.String(3), server_default="EUR"),
            sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("vendor_id", "sku", name="u_vendor_sku"),
        )
    if "keepa_offers" not in tables:
        op.create_table(
            "keepa_offers", sa.Column("asin", sa.Text(), primary_key=True), sa.Column("buybox_price", sa.Numeric(10, 2))
        )
    op.execute(
        """
        DROP VIEW IF EXISTS roi_view CASCADE;
        DROP VIEW IF EXISTS v_roi_full CASCADE;
        """
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
    op.execute("CREATE OR REPLACE VIEW roi_view AS SELECT asin, roi_pct FROM v_roi_full;")


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_roi_full CASCADE;")
    op.drop_table("keepa_offers")
    op.drop_table("vendor_prices")
    op.drop_table("vendors")
