import sqlalchemy as sa
import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op  # type: ignore[attr-defined]

revision = "0004_fee_cron"
down_revision = "0003_vendor_prices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("fees_raw")}

    # 0 – drop outdated views so column rename succeeds
    op.execute(
        """
        DROP VIEW IF EXISTS roi_view CASCADE;
        DROP VIEW IF EXISTS v_roi_full CASCADE;
        """
    )

    # 1 – rename fulf_fee ➜ fulfil_fee so view will work
    if "fulf_fee" in cols and "fulfil_fee" not in cols:
        op.alter_column(
            "fees_raw",
            "fulf_fee",
            new_column_name="fulfil_fee",
            existing_type=sa.Numeric(10, 2),
            existing_nullable=False,
        )

    # 2 – add new columns idempotently
    if "storage_fee" not in cols:
        op.add_column(
            "fees_raw",
            sa.Column(
                "storage_fee", sa.Numeric(10, 2), nullable=False, server_default="0"
            ),
        )
    if "currency" not in cols:
        op.add_column(
            "fees_raw",
            sa.Column("currency", sa.String(3), nullable=False, server_default="€"),
        )
    if "updated_at" not in cols:
        op.add_column(
            "fees_raw",
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )

    # 3 – re-create roi_view with correct column name
    op.execute(
        """
        DROP VIEW IF EXISTS roi_view CASCADE;
        DROP VIEW IF EXISTS v_roi_full CASCADE;
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

    op.execute(
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


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_roi_full CASCADE;")
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("fees_raw")}
    if "fulfil_fee" in cols and "fulf_fee" not in cols:
        op.alter_column(
            "fees_raw",
            "fulfil_fee",
            new_column_name="fulf_fee",
            existing_type=sa.Numeric(10, 2),
            existing_nullable=False,
        )
    if "updated_at" in cols:
        op.drop_column("fees_raw", "updated_at")
    if "currency" in cols:
        op.drop_column("fees_raw", "currency")
    if "storage_fee" in cols:
        op.drop_column("fees_raw", "storage_fee")
    op.execute(
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
        JOIN keepa_offers k ON k.asin = p.asin
        JOIN fees_raw      f ON f.asin = p.asin;
        """
    )

    op.execute(
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
