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
    # TODO: confirm restored content


def downgrade() -> None:
    op.drop_table("buybox")
    # TODO: confirm restored content

