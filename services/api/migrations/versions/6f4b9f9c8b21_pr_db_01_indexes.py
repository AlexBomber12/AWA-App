from __future__ import annotations

import sqlalchemy as sa
from alembic import op  # type: ignore[attr-defined]

revision = "6f4b9f9c8b21"
down_revision = "6ea19ad3bc8a"
branch_labels = None
depends_on = None

ROI_SCHEMA = "public"
ROI_VIEW = "mat_v_roi_full"
VENDOR_PRICES_TABLE = "vendor_prices"
PRODUCTS_TABLE = "products"
RETURNS_TABLE = "returns_raw"
RETURNS_SCHEMA = "public"


def upgrade() -> None:
    _create_roi_indexes()
    _create_returns_indexes()


def downgrade() -> None:
    _drop_returns_indexes()
    _drop_roi_indexes()


def _connection():
    return op.get_bind()


def _run_ddl(sql: str) -> None:
    ctx = op.get_context()
    conn = _connection()
    with ctx.autocommit_block():
        conn.execute(sa.text(sql))


def _table_exists(schema: str, table: str) -> bool:
    stmt = sa.text(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = :schema AND table_name = :table
        LIMIT 1
        """
    )
    result = _connection().execute(stmt, {"schema": schema, "table": table})
    return result.scalar() is not None


def _create_roi_indexes() -> None:
    if not _table_exists(ROI_SCHEMA, ROI_VIEW):
        return
    _run_ddl(
        f"""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_mat_v_roi_full_roi_pct_asin
        ON {ROI_SCHEMA}.{ROI_VIEW} USING btree (roi_pct DESC, asin)
        """
    )
    if _table_exists(ROI_SCHEMA, PRODUCTS_TABLE):
        _run_ddl(
            f"""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_products_category_lower_asin
            ON {ROI_SCHEMA}.{PRODUCTS_TABLE} (LOWER(category), asin)
            """
        )
    if _table_exists(ROI_SCHEMA, VENDOR_PRICES_TABLE):
        _run_ddl(
            f"""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_vendor_prices_vendor_sku
            ON {ROI_SCHEMA}.{VENDOR_PRICES_TABLE} (vendor_id, sku)
            """
        )
    _run_ddl(f"ANALYZE {ROI_SCHEMA}.{ROI_VIEW}")


def _drop_roi_indexes() -> None:
    _run_ddl("DROP INDEX IF EXISTS ix_mat_v_roi_full_roi_pct_asin")
    _run_ddl("DROP INDEX IF EXISTS ix_products_category_lower_asin")
    _run_ddl("DROP INDEX IF EXISTS ix_vendor_prices_vendor_sku")


def _create_returns_indexes() -> None:
    if not _table_exists(RETURNS_SCHEMA, RETURNS_TABLE):
        return
    _run_ddl(
        f"""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_returns_raw_asin
        ON {RETURNS_SCHEMA}.{RETURNS_TABLE} (asin)
        """
    )
    _run_ddl(f"ANALYZE {RETURNS_SCHEMA}.{RETURNS_TABLE}")


def _drop_returns_indexes() -> None:
    _run_ddl("DROP INDEX IF EXISTS ix_returns_raw_asin")
