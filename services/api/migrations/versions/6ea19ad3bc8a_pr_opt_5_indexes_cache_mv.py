from __future__ import annotations

import datetime as dt
import os
from collections.abc import Iterable, Sequence

import sqlalchemy as sa
from alembic import op  # type: ignore[attr-defined]

revision = "6ea19ad3bc8a"
down_revision = "0032_etl_reliability"
branch_labels = None
depends_on = None

RETURNS_SCHEMA = "public"
RETURNS_TABLE = "returns_raw"
RETURNS_PARTITION_PARENT = "returns_raw_partitioned"
PARTITION_ENV = "RETURNS_PARTITION_SCAFFOLD"
PARTITION_MONTHS_BACK = 1
PARTITION_MONTHS_FORWARD = 5
ROI_VIEW = "mat_v_roi_full"
ROI_SCHEMA = "public"
TREND_DATE_CANDIDATES: Sequence[str] = ("dt", "date", "snapshot_date", "created_at")


def upgrade() -> None:
    _create_returns_indexes()
    _create_roi_view_indexes()
    _maybe_prepare_returns_partition_scaffold()


def downgrade() -> None:
    _drop_roi_view_indexes()
    _drop_returns_partition_scaffold()
    _drop_returns_indexes()


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").lower() in {"1", "true", "yes", "on"}


def _column_exists(conn: sa.engine.Connection, *, schema: str, table: str, column: str) -> bool:
    stmt = sa.text(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = :schema AND table_name = :table AND column_name = :column
        LIMIT 1
        """
    )
    result = conn.execute(stmt, {"schema": schema, "table": table, "column": column})
    return result.scalar() is not None


def _table_exists(conn: sa.engine.Connection, *, schema: str, table: str) -> bool:
    stmt = sa.text(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = :schema AND table_name = :table
        LIMIT 1
        """
    )
    result = conn.execute(stmt, {"schema": schema, "table": table})
    return result.scalar() is not None


def _run_ddl(sql: str) -> None:
    ctx = op.get_context()
    conn = op.get_bind()
    with ctx.autocommit_block():
        conn.execute(sa.text(sql))


def _analyze(fqname: str) -> None:
    _run_ddl(f"ANALYZE {fqname}")


def _create_returns_indexes() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, schema=RETURNS_SCHEMA, table=RETURNS_TABLE):
        return

    indexes: list[tuple[str, str, bool]] = [
        (
            "ix_returns_raw_vendor_date_asin",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_returns_raw_vendor_date_asin "
            "ON {schema}.{table} USING btree (vendor, return_date, asin)",
            _column_exists(conn, schema=RETURNS_SCHEMA, table=RETURNS_TABLE, column="vendor"),
        ),
        (
            "ix_returns_raw_date_asin",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_returns_raw_date_asin "
            "ON {schema}.{table} USING btree (return_date, asin)",
            _column_exists(conn, schema=RETURNS_SCHEMA, table=RETURNS_TABLE, column="return_date"),
        ),
        (
            "ix_returns_raw_vendor",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_returns_raw_vendor ON {schema}.{table} USING btree (vendor)",
            _column_exists(conn, schema=RETURNS_SCHEMA, table=RETURNS_TABLE, column="vendor"),
        ),
    ]

    for _, template, enabled in indexes:
        if not enabled:
            continue
        sql = template.format(schema=RETURNS_SCHEMA, table=RETURNS_TABLE)
        _run_ddl(sql)

    _analyze(f"{RETURNS_SCHEMA}.{RETURNS_TABLE}")


def _drop_returns_indexes() -> None:
    drop_statements = [
        "DROP INDEX IF EXISTS ix_returns_raw_vendor_date_asin",
        "DROP INDEX IF EXISTS ix_returns_raw_date_asin",
        "DROP INDEX IF EXISTS ix_returns_raw_vendor",
    ]
    for stmt in drop_statements:
        _run_ddl(stmt)


def _create_roi_view_indexes() -> None:
    conn = op.get_bind()
    if not _table_exists(conn, schema=ROI_SCHEMA, table=ROI_VIEW):
        return

    if _column_exists(conn, schema=ROI_SCHEMA, table=ROI_VIEW, column="vendor"):
        _run_ddl(
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_mat_v_roi_full_vendor "
            f"ON {ROI_SCHEMA}.{ROI_VIEW} USING btree (vendor)"
        )

    for column in TREND_DATE_CANDIDATES:
        if _column_exists(conn, schema=ROI_SCHEMA, table=ROI_VIEW, column=column):
            _run_ddl(
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_mat_v_roi_full_{column} "
                f"ON {ROI_SCHEMA}.{ROI_VIEW} USING btree ({column})"
            )
            break

    _analyze(f"{ROI_SCHEMA}.{ROI_VIEW}")


def _drop_roi_view_indexes() -> None:
    statements = [
        "DROP INDEX IF EXISTS ix_mat_v_roi_full_vendor",
        "DROP INDEX IF EXISTS ix_mat_v_roi_full_snapshot_date",
        "DROP INDEX IF EXISTS ix_mat_v_roi_full_dt",
        "DROP INDEX IF EXISTS ix_mat_v_roi_full_date",
        "DROP INDEX IF EXISTS ix_mat_v_roi_full_created_at",
    ]
    for stmt in statements:
        _run_ddl(stmt)


def _maybe_prepare_returns_partition_scaffold() -> None:
    if not _truthy_env(PARTITION_ENV):
        return
    conn = op.get_bind()
    if not _column_exists(conn, schema=RETURNS_SCHEMA, table=RETURNS_TABLE, column="return_date"):
        return

    _run_ddl(
        f"""
        CREATE TABLE IF NOT EXISTS {RETURNS_SCHEMA}.{RETURNS_PARTITION_PARENT}
        (LIKE {RETURNS_SCHEMA}.{RETURNS_TABLE} INCLUDING ALL)
        PARTITION BY RANGE (return_date)
        """
    )

    for year, month in _partition_months():
        child = f"{RETURNS_SCHEMA}.returns_raw_{year}_{month:02d}"
        start = dt.date(year, month, 1)
        end = _month_end(start)
        _run_ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {child}
            PARTITION OF {RETURNS_SCHEMA}.{RETURNS_PARTITION_PARENT}
            FOR VALUES FROM ('{start:%Y-%m-%d}') TO ('{end:%Y-%m-%d}')
            """
        )


def _drop_returns_partition_scaffold() -> None:
    if not _table_exists(op.get_bind(), schema=RETURNS_SCHEMA, table=RETURNS_PARTITION_PARENT):
        return
    _run_ddl(f"DROP TABLE IF EXISTS {RETURNS_SCHEMA}.{RETURNS_PARTITION_PARENT} CASCADE")


def _partition_months(
    *,
    today: dt.date | None = None,
    months_back: int = PARTITION_MONTHS_BACK,
    months_forward: int = PARTITION_MONTHS_FORWARD,
) -> Iterable[tuple[int, int]]:
    anchor = today or dt.date.today()
    start_offset = -months_back
    total = months_back + months_forward + 1
    for offset in range(start_offset, start_offset + total):
        current = _shift_month(anchor, offset)
        yield current.year, current.month


def _shift_month(anchor: dt.date, offset: int) -> dt.date:
    month_index = anchor.month - 1 + offset
    year = anchor.year + month_index // 12
    month = month_index % 12 + 1
    return dt.date(year, month, 1)


def _month_end(start: dt.date) -> dt.date:
    if start.month == 12:
        return dt.date(start.year + 1, 1, 1)
    return dt.date(start.year, start.month + 1, 1)
