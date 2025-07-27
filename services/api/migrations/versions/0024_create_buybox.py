"""create buybox & rebuild roi_view"""

import sqlalchemy as sa
from alembic import op

revision = "0024_create_buybox"
down_revision = "0023_add_storage_fee"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "buybox",
        sa.Column("asin", sa.String(10), primary_key=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("captured_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )

    op.execute("DROP VIEW IF EXISTS roi_view")
    op.execute(
        """
        CREATE VIEW roi_view AS
        SELECT p.asin,
               f.fulfil_fee,
               f.referral_fee,
               COALESCE(f.storage_fee, 0)  AS storage_fee,
               b.price,
               (b.price - f.fulfil_fee - f.referral_fee - COALESCE(f.storage_fee,0)) AS margin
        FROM products p
        JOIN fees_raw f ON p.asin = f.asin
        JOIN buybox   b ON p.asin = b.asin;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW roi_view")
    op.drop_table("buybox")
