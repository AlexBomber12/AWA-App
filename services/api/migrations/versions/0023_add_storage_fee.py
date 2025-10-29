import sys
from pathlib import Path
from textwrap import dedent

import sqlalchemy as sa
from alembic import op  # type: ignore[attr-defined]
from sqlalchemy import inspect

sys.path.append(str(Path(__file__).resolve().parents[4]))
from services.db.utils.views import replace_view

revision = "0023_add_storage_fee"
down_revision = "0022_fix_roi_view"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("fees_raw")}
    if "storage_fee" not in cols:
        op.add_column("fees_raw", sa.Column("storage_fee", sa.Numeric(10, 2)))


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("fees_raw")}
    if "storage_fee" in cols:
        # Drop dependent view first to avoid dependency errors when dropping the column
        op.execute("DROP VIEW IF EXISTS v_roi_full CASCADE")
        op.drop_column("fees_raw", "storage_fee")
        replace_view(
            "v_roi_full",
            dedent(
                """
                CREATE OR REPLACE VIEW v_roi_full AS
                SELECT
                  p.asin,
                  vp.cost,
                  f.fulfil_fee,
                  f.referral_fee,
                  0 AS storage_fee,
                  k.buybox_price,
                  ROUND(
                    100 * (
                      k.buybox_price
                      - (f.fulfil_fee + f.referral_fee)
                      - vp.cost
                      - COALESCE(rt.refunds, 0)
                      + COALESCE(rbt.reimbursements, 0)
                    ) / NULLIF(vp.cost, 0),
                    1
                  ) AS roi_pct
                FROM products p
                JOIN (
                  SELECT v1.*
                  FROM vendor_prices v1
                  JOIN (
                    SELECT sku, MAX(updated_at) AS max_ts
                    FROM vendor_prices
                    GROUP BY sku
                  ) v2 ON v2.sku = v1.sku AND v2.max_ts = v1.updated_at
                ) vp ON vp.sku = p.asin
                JOIN fees_raw f ON f.asin = p.asin
                JOIN keepa_offers k ON k.asin = p.asin
                LEFT JOIN v_refund_totals rt ON rt.asin = p.asin
                LEFT JOIN v_reimb_totals rbt ON rbt.asin = p.asin;
                """
            ),
        )
