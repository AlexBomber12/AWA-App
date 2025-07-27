"""add storage_fee to fees_raw and roi_view"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op  # type: ignore[attr-defined]

revision = "0023_add_storage_fee"
down_revision = "0022_fix_roi_view"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("fees_raw")}
    if "storage_fee" not in cols:
        op.add_column("fees_raw", sa.Column("storage_fee", sa.Numeric(10, 2)))
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute(
        """
        CREATE VIEW roi_view AS
        SELECT p.asin,
               f.fulfil_fee,
               f.referral_fee,
               f.storage_fee,
               (bb.price - f.fulfil_fee - f.referral_fee - f.storage_fee) AS margin
          FROM products p
          JOIN fees_raw f ON p.asin = f.asin
          JOIN buybox bb ON p.asin = bb.asin;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute(
        """
        CREATE VIEW roi_view AS
        SELECT p.asin,
               f.fulfil_fee,
               f.referral_fee,
               (bb.price - f.fulfil_fee - f.referral_fee) AS margin
          FROM products p
          JOIN fees_raw f ON p.asin = f.asin
          JOIN buybox bb ON p.asin = bb.asin;
        """
    )
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("fees_raw")}
    if "storage_fee" in cols:
        op.drop_column("fees_raw", "storage_fee")
