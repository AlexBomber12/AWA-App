import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op  # type: ignore[attr-defined]

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = inspect(bind).get_table_names()

    if "products" not in tables:
        op.create_table(
            "products",
            sa.Column("asin", sa.TEXT(), primary_key=True),
            sa.Column("title", sa.TEXT()),
            sa.Column("brand", sa.TEXT()),
            sa.Column("category", sa.TEXT()),
            sa.Column("weight_kg", sa.Numeric()),
        )
    if "offers" not in tables:
        op.create_table(
            "offers",
            sa.Column("asin", sa.TEXT(), sa.ForeignKey("products.asin")),
            sa.Column("seller_sku", sa.TEXT()),
            sa.Column("price_cents", sa.Integer()),
            sa.Column("captured_at", sa.TIMESTAMP(timezone=True)),
        )
    if "fees_raw" not in tables:
        op.create_table(
            "fees_raw",
            sa.Column("asin", sa.TEXT(), primary_key=True),
            sa.Column("fulf_fee", sa.Numeric()),
            sa.Column("referral_fee", sa.Numeric()),
            sa.Column("storage_fee", sa.Numeric()),
            sa.Column("captured_at", sa.TIMESTAMP(timezone=True)),
        )
    if "etl_log" not in tables:
        op.create_table(
            "etl_log",
            sa.Column("job", sa.TEXT()),
            sa.Column(
                "run_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
            ),
            sa.Column("row_cnt", sa.Integer()),
        )
    op.execute(
        """
        CREATE VIEW roi_view AS
        SELECT
          p.asin,
          MAX(o.price_cents) / 100.0
              - f.fulf_fee
              - f.referral_fee
              - f.storage_fee        AS roi_eur
        FROM products p
        JOIN offers   o ON o.asin = p.asin
        JOIN fees_raw f ON f.asin = p.asin
        GROUP BY p.asin, f.fulf_fee, f.referral_fee, f.storage_fee;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.drop_table("etl_log")
    op.drop_table("fees_raw")
    op.drop_table("offers")
    op.drop_table("products")
