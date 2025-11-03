from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import text

from services.worker.maintenance import task_refresh_roi_mvs

pytestmark = [pytest.mark.integration]


def _select_scalar(conn, query: str, **params):
    result = conn.execute(text(query), params)
    return result.scalar()


def test_materialized_views_are_materialized_and_indexed(db_engine):
    asin = "MVTEST001"

    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM vendor_prices WHERE sku = :asin"), {"asin": asin})
        conn.execute(text("DELETE FROM fees_raw WHERE asin = :asin"), {"asin": asin})
        conn.execute(text("DELETE FROM keepa_offers WHERE asin = :asin"), {"asin": asin})
        conn.execute(text("DELETE FROM returns_raw WHERE asin = :asin"), {"asin": asin})
        conn.execute(text("DELETE FROM reimbursements_raw WHERE asin = :asin"), {"asin": asin})
        conn.execute(text("DELETE FROM products WHERE asin = :asin"), {"asin": asin})

        conn.execute(
            text(
                """
                INSERT INTO products (asin, title, category, weight_kg)
                VALUES (:asin, 'Integration Test Product', 'Test', 1.0)
                """
            ),
            {"asin": asin},
        )
        conn.execute(
            text(
                """
                INSERT INTO vendors (id, name)
                VALUES (999, 'integration-test-vendor')
                ON CONFLICT (id) DO NOTHING
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO vendor_prices (vendor_id, sku, cost, updated_at)
                VALUES (999, :asin, 10.0, :ts)
                """
            ),
            {"asin": asin, "ts": datetime(2024, 1, 1)},
        )
        conn.execute(
            text(
                """
                INSERT INTO fees_raw (
                    asin, fulfil_fee, referral_fee, storage_fee,
                    currency, captured_at, updated_at
                )
                VALUES (
                    :asin, 1.5, 2.5, 0.5,
                    'EUR', :ts, :ts
                )
                """
            ),
            {"asin": asin, "ts": datetime(2024, 1, 1)},
        )
        conn.execute(
            text(
                """
                INSERT INTO keepa_offers (asin, buybox_price)
                VALUES (:asin, 25.0)
                """
            ),
            {"asin": asin},
        )
        conn.execute(
            text(
                """
                INSERT INTO returns_raw (id, asin, qty, refund_amount, return_date)
                VALUES (9991, :asin, 1, 3.0, '2024-01-04')
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"asin": asin},
        )
        conn.execute(
            text(
                """
                INSERT INTO reimbursements_raw (id, asin, amount, reimb_date)
                VALUES (9992, :asin, 1.0, '2024-01-05')
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"asin": asin},
        )

    result = task_refresh_roi_mvs.run()  # type: ignore[attr-defined]
    assert result["status"] == "success"
    assert set(result["views"]) == {"mat_v_roi_full", "mat_fees_expanded"}

    with db_engine.connect() as conn:
        assert _select_scalar(conn, "SELECT to_regclass('mat_v_roi_full')") is not None
        assert _select_scalar(conn, "SELECT to_regclass('mat_fees_expanded')") is not None

        roi_index_exists = _select_scalar(
            conn,
            """
            SELECT 1
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'mat_v_roi_full'
              AND indexname = 'ix_mat_v_roi_full_pk'
            """,
        )
        fees_index_exists = _select_scalar(
            conn,
            """
            SELECT 1
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'mat_fees_expanded'
              AND indexname = 'ix_mat_fees_expanded_pk'
            """,
        )
        assert roi_index_exists == 1
        assert fees_index_exists == 1

        conn.execute(text("SELECT * FROM v_roi_full LIMIT 0"))
        rows = conn.execute(
            text("SELECT asin, roi_pct FROM v_roi_full WHERE asin = :asin"),
            {"asin": asin},
        ).fetchall()
        assert rows

        count = _select_scalar(conn, "SELECT COUNT(*) FROM mat_v_roi_full")
        if not count:
            pytest.skip("mat_v_roi_full is empty; skipping planner analysis")

        with conn.begin():
            conn.execute(text("SET LOCAL enable_seqscan=off"))
            plan_rows = conn.execute(
                text("EXPLAIN SELECT * FROM mat_v_roi_full WHERE asin = :asin"),
                {"asin": asin},
            ).fetchall()
        plan_text = " ".join(row[0] for row in plan_rows)
        assert "Index Scan" in plan_text or "Index Only Scan" in plan_text
