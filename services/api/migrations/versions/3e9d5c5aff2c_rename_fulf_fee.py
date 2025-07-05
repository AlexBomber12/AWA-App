from alembic import op  # type: ignore[attr-defined]
from sqlalchemy import inspect

"""rename fulf_fee -> fulfil_fee and recreate roi_view (fixed id)"""

revision = "3e9d5c5aff2c"
down_revision = "0002_create_roi_view"
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # drop view first so renaming fees_raw succeeds
    op.execute("DROP VIEW IF EXISTS roi_view")

    # clean leftovers from failed runs
    tables = {t for t in inspect(bind).get_table_names()}
    if "_alembic_tmp_fees_raw" in tables:
        op.execute("DROP TABLE _alembic_tmp_fees_raw")

    cols = {c["name"] for c in inspect(bind).get_columns("fees_raw")}
    if "fulf_fee" in cols and "fulfil_fee" not in cols:
        with op.batch_alter_table("fees_raw") as batch:
            batch.alter_column("fulf_fee", new_column_name="fulfil_fee")

    op.execute(
        """
        CREATE VIEW roi_view AS
        SELECT
            p.asin,
            MAX(o.price_cents) / 100.0
              - f.fulfil_fee
              - f.referral_fee
              - f.storage_fee AS roi_eur
        FROM products p
        JOIN offers   o ON o.asin = p.asin
        JOIN fees_raw f ON f.asin  = p.asin
        GROUP BY p.asin, f.fulfil_fee, f.referral_fee, f.storage_fee
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW roi_view")
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("fees_raw")}
    if "fulfil_fee" in cols and "fulf_fee" not in cols:
        with op.batch_alter_table("fees_raw") as batch:
            batch.alter_column("fulfil_fee", new_column_name="fulf_fee")
