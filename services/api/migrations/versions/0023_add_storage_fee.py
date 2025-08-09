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
    # TODO: confirm restored content


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("fees_raw")}
    if "storage_fee" in cols:
        op.drop_column("fees_raw", "storage_fee")
    # TODO: confirm restored content

