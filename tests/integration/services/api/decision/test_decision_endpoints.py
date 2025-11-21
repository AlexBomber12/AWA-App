from __future__ import annotations

import pytest
from sqlalchemy import text

import services.api.security as security
from awa_common.security.models import Role, UserCtx
from services.api.main import app

pytestmark = pytest.mark.integration


@pytest.fixture
def allow_admin_user(fastapi_dep_overrides, dummy_user_ctx):
    user = dummy_user_ctx(roles=[Role.admin])

    async def _admin():
        return user

    def _limit_provider():
        async def _noop(_request):
            return None

        return _noop

    with fastapi_dep_overrides(
        app,
        **{
            security.require_admin: _admin,
            security.require_ops: _admin,
            security.limit_ops: _limit_provider,
        },
    ):
        yield user


def _seed_roi_rows(db_engine, asin: str, vendor_id: int) -> None:
    with db_engine.begin() as conn:
        conn.execute(
            text("DELETE FROM events WHERE task_id IN (SELECT id FROM tasks WHERE asin = :asin)"), {"asin": asin}
        )
        conn.execute(text("DELETE FROM tasks WHERE asin = :asin"), {"asin": asin})
        conn.execute(text("DELETE FROM vendor_prices WHERE sku = :asin"), {"asin": asin})
        conn.execute(text("DELETE FROM keepa_offers WHERE asin = :asin"), {"asin": asin})
        conn.execute(text("DELETE FROM fees_raw WHERE asin = :asin"), {"asin": asin})
        conn.execute(text("DELETE FROM products WHERE asin = :asin"), {"asin": asin})
        conn.execute(
            text(
                """
                INSERT INTO products (asin, title, category, weight_kg)
                VALUES (:asin, 'Decision Test SKU', 'test', 1.0)
                ON CONFLICT (asin) DO UPDATE SET title = EXCLUDED.title, category = EXCLUDED.category
                """
            ),
            {"asin": asin},
        )
        conn.execute(
            text(
                """
                INSERT INTO vendors (id, name)
                VALUES (:vendor_id, 'Decision Vendor')
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                """
            ),
            {"vendor_id": vendor_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO vendor_prices (vendor_id, sku, cost, updated_at)
                VALUES (:vendor_id, :asin, 18.0, NOW())
                ON CONFLICT (vendor_id, sku) DO UPDATE SET cost = EXCLUDED.cost, updated_at = EXCLUDED.updated_at
                """
            ),
            {"vendor_id": vendor_id, "asin": asin},
        )
        conn.execute(
            text(
                """
                INSERT INTO keepa_offers (asin, buybox_price)
                VALUES (:asin, 12.0)
                ON CONFLICT (asin) DO UPDATE SET buybox_price = EXCLUDED.buybox_price
                """
            ),
            {"asin": asin},
        )
        conn.execute(
            text(
                """
                INSERT INTO fees_raw (asin, fulfil_fee, referral_fee, storage_fee, currency, captured_at, updated_at)
                VALUES (:asin, 1.0, 1.0, 0.5, 'EUR', NOW(), NOW())
                ON CONFLICT (asin) DO UPDATE SET
                    fulfil_fee = EXCLUDED.fulfil_fee,
                    referral_fee = EXCLUDED.referral_fee,
                    storage_fee = EXCLUDED.storage_fee,
                    updated_at = NOW()
                """
            ),
            {"asin": asin},
        )
        conn.execute(text("REFRESH MATERIALIZED VIEW mat_v_roi_full"))


def test_decision_run_creates_tasks(api_client, db_engine, allow_admin_user: UserCtx):
    asin = "DECISION-001"
    vendor_id = 991
    _seed_roi_rows(db_engine, asin, vendor_id)

    run_response = api_client.post("/decision/run", params={"limit": 10})
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["pagination"]["total"] >= 1
    created = payload["items"][0]
    assert created["entity"]["asin"] == asin

    inbox_response = api_client.get("/inbox/tasks", params={"taskId": created["id"]})
    assert inbox_response.status_code == 200
    body = inbox_response.json()
    assert body["pagination"]["total"] == 1
    assert body["items"][0]["decision"] in {"request_price", "request_discount"}
    assert body["items"][0]["state"] in {"open", "pending"}
