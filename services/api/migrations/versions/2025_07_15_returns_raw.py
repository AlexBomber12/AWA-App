from textwrap import dedent

from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "2025_07_15_returns_raw"
down_revision = "0005_add_mv_indexes"
branch_labels = depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = inspect(bind).get_table_names()
    if "returns_raw" not in tables:
        op.create_table(
            "returns_raw",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("asin", sa.Text, sa.ForeignKey("products.asin"), nullable=False),
            sa.Column("qty", sa.Integer, nullable=False),
            sa.Column("fee_eur", sa.Numeric(10, 2), nullable=False),
            sa.Column("processed_at", sa.Date, nullable=False),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.func.now(),
            ),
        )

    op.execute(
        dedent(
            """
            CREATE OR REPLACE VIEW v_returns AS
            SELECT asin, SUM(fee_eur) AS total_fee_eur
              FROM returns_raw
             GROUP BY asin;
            """
        )
    )

    op.execute("DROP VIEW IF EXISTS v_roi_full")
    op.execute(
        dedent(
            """
            CREATE VIEW v_roi_full AS
            SELECT p.asin,
                   vp.cost,
                   f.fulfil_fee,
                   f.referral_fee,
                   f.storage_fee,
                   fr.eur_per_kg * COALESCE(p.weight_kg, 0) AS freight,
                   k.buybox_price,
                   ROUND(
                     100 * (
                       k.buybox_price
                       - vp.cost
                       - f.fulfil_fee
                       - f.referral_fee
                       - f.storage_fee
                       - fr.eur_per_kg * COALESCE(p.weight_kg, 0)
                       - COALESCE(vr.total_fee_eur, 0)
                     ) / vp.cost,
                   1) AS roi_pct
            FROM products p
            JOIN vendor_prices vp ON vp.sku = p.asin
            JOIN fees_raw      f  ON f.asin = p.asin
            JOIN freight_rates fr ON fr.lane='EU→IT' AND fr.mode='sea'
            JOIN keepa_offers  k  ON k.asin = p.asin
            LEFT JOIN v_returns vr ON vr.asin = p.asin;
            """
        )
    )
    op.execute("CREATE OR REPLACE VIEW roi_view AS SELECT asin, roi_pct FROM v_roi_full")


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute("DROP VIEW IF EXISTS v_roi_full")
    op.execute("DROP VIEW IF EXISTS v_returns")
    op.drop_table("returns_raw")
