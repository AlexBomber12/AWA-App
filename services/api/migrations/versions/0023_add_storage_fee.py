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
    # In earlier migrations we only created a ``keepa_offers`` table with a
    # ``buybox_price`` column.  The ``buybox`` table referenced in this
    # migration never existed, which caused runtime failures when Alembic
    # attempted to build the ROI view.  To retain the intended schema while
    # keeping backwards compatibility, we create a lightweight view named
    # ``buybox`` that simply exposes the ``buybox_price`` column under the
    # expected ``price`` alias.  If the view already exists it will be
    # replaced.
    op.execute(
        """
        CREATE OR REPLACE VIEW buybox AS
        SELECT asin, buybox_price AS price
          FROM keepa_offers;
        """
    )

    # Recreate the ROI view to incorporate the new ``storage_fee`` column.  The
    # margin calculation now references our ``buybox`` view rather than a
    # missing table.  Dropping the existing view first ensures that the
    # statement is idempotent when migrations are run multiple times.
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
    # Remove the ROI view so that we can safely modify or drop the ``buybox`` view.
    op.execute("DROP VIEW IF EXISTS roi_view")

    # Restore the previous definition of the ROI view which did not include
    # ``storage_fee`` in the margin calculation.  We join directly to
    # ``keepa_offers`` here rather than the ``buybox`` view because prior
    # revisions never created that view.  The join uses ``buybox_price`` as
    # the selling price.
    op.execute(
        """
        CREATE VIEW roi_view AS
        SELECT p.asin,
               f.fulfil_fee,
               f.referral_fee,
               (k.buybox_price - f.fulfil_fee - f.referral_fee) AS margin
          FROM products p
          JOIN fees_raw f ON p.asin = f.asin
          JOIN keepa_offers k ON p.asin = k.asin;
        """
    )

    # Drop the ``buybox`` view since earlier revisions did not define it
    op.execute("DROP VIEW IF EXISTS buybox")

    # Finally, remove the ``storage_fee`` column if present to return the
    # ``fees_raw`` table to its original shape.
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("fees_raw")}
    if "storage_fee" in cols:
        op.drop_column("fees_raw", "storage_fee")
