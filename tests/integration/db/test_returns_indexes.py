from __future__ import annotations

import pytest
from sqlalchemy import text

pytestmark = [pytest.mark.integration]


def _index_exists(conn, name: str) -> bool:
    return bool(conn.execute(text("SELECT to_regclass(:name)"), {"name": name}).scalar())


def _vendor_column_exists(conn) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'returns_raw'
                  AND column_name = 'vendor'
                """
            )
        ).scalar()
    )


def test_returns_indexes_created(db_engine):
    with db_engine.connect() as conn:
        assert _index_exists(conn, "ix_returns_raw_date_asin")
        vendor_available = _vendor_column_exists(conn)
        if vendor_available:
            assert _index_exists(conn, "ix_returns_raw_vendor")
            assert _index_exists(conn, "ix_returns_raw_vendor_date_asin")


def test_returns_explain_uses_vendor_index(db_engine):
    with db_engine.begin() as conn:
        if not _vendor_column_exists(conn):
            pytest.skip("returns_raw.vendor missing; vendor index not created")
        conn.execute(text("ANALYZE returns_raw"))
        conn.execute(text("SET LOCAL enable_seqscan = off"))
        plan_rows = conn.execute(
            text(
                """
                EXPLAIN
                SELECT asin
                FROM returns_raw
                WHERE vendor = 'explain-test'
                  AND return_date BETWEEN '2024-01-01' AND '2024-02-01'
                """
            )
        ).fetchall()
        plan_text = " ".join(row[0] for row in plan_rows)
        assert "ix_returns_raw_vendor_date_asin" in plan_text or "ix_returns_raw_vendor" in plan_text
