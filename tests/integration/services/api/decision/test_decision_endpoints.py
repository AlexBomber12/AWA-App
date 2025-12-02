from __future__ import annotations

import json

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
            security.require_viewer: _admin,
            security.limit_ops: _limit_provider,
            security.limit_viewer: _limit_provider,
        },
    ):
        yield user


def _seed_roi_rows(db_engine, asin: str, vendor_id: int, *, cost: float = 18.0, buybox_price: float = 12.0) -> None:
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
                VALUES (:vendor_id, :asin, :cost, NOW())
                ON CONFLICT (vendor_id, sku) DO UPDATE SET cost = EXCLUDED.cost, updated_at = EXCLUDED.updated_at
                """
            ),
            {"vendor_id": vendor_id, "asin": asin, "cost": cost},
        )
        conn.execute(
            text(
                """
                INSERT INTO keepa_offers (asin, buybox_price)
                VALUES (:asin, :buybox_price)
                ON CONFLICT (asin) DO UPDATE SET buybox_price = EXCLUDED.buybox_price
                """
            ),
            {"asin": asin, "buybox_price": buybox_price},
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


def _insert_manual_task(
    db_engine, asin: str, vendor_id: int, decision: str = "audit_pricing", priority: int = 60
) -> str:
    with db_engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO tasks (
                    source,
                    entity_type,
                    asin,
                    vendor_id,
                    entity,
                    decision,
                    priority,
                    state,
                    why,
                    alternatives,
                    links
                )
                VALUES (
                    'manual',
                    'sku_vendor',
                    :asin,
                    :vendor_id,
                    :entity::jsonb,
                    :decision,
                    :priority,
                    'pending',
                    :why::jsonb,
                    '[]'::jsonb,
                    :links::jsonb
                )
                RETURNING id
                """
            ),
            {
                "asin": asin,
                "vendor_id": vendor_id,
                "entity": json.dumps({"type": "sku_vendor", "asin": asin, "vendor_id": vendor_id}),
                "decision": decision,
                "priority": priority,
                "why": json.dumps([{"code": "audit_requested", "message": "Manual audit requested"}]),
                "links": json.dumps({"asin": asin, "vendor_id": vendor_id}),
            },
        )
    return str(result.scalar_one())


def _ensure_freight_rate(db_engine) -> None:
    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM freight_rates WHERE lane = 'EU→IT' AND mode = 'sea'"))
        conn.execute(
            text(
                """
                INSERT INTO freight_rates(lane, mode, eur_per_kg)
                VALUES ('EU→IT', 'sea', 1.0)
                ON CONFLICT (lane, mode) DO UPDATE SET eur_per_kg = EXCLUDED.eur_per_kg
                """
            )
        )


def test_decision_run_creates_tasks(api_client, db_engine, allow_admin_user: UserCtx):
    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM events"))
        conn.execute(text("DELETE FROM tasks"))
    asin = "DECISION-001"
    vendor_id = 991
    _seed_roi_rows(db_engine, asin, vendor_id)

    run_response = api_client.post("/decision/run", params={"limit": 10})
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["pagination"]["total"] >= 1
    created = payload["items"][0]
    assert created["entity"]["asin"] == asin
    assert created["links"]["asin"] == asin
    assert created["links"]["vendor_id"] == vendor_id
    assert created["status"] == "open"
    assert created["why"][0]["code"].startswith("roi_")

    inbox_response = api_client.get("/inbox/tasks", params={"taskId": created["id"]})
    assert inbox_response.status_code == 200
    body = inbox_response.json()
    assert body["pagination"]["total"] == 1
    assert body["items"][0]["decision"] in {"request_price", "request_discount"}
    assert body["items"][0]["state"] in {"open", "pending"}
    assert body["items"][0]["status"] == body["items"][0]["state"]


def test_inbox_pagination_and_multi_tasks(api_client, db_engine, allow_admin_user: UserCtx):
    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM events"))
        conn.execute(text("DELETE FROM tasks"))
    asin = "DECISION-002"
    vendor_primary = 993
    vendor_secondary = 994
    _seed_roi_rows(db_engine, asin, vendor_primary, cost=18.0, buybox_price=11.5)  # critical ROI
    _seed_roi_rows(db_engine, "DECISION-003", 995, cost=9.0, buybox_price=12.0)  # lower priority task
    manual_task_id = _insert_manual_task(db_engine, asin, vendor_secondary, priority=65)

    run_response = api_client.post("/decision/run", params={"limit": 10})
    assert run_response.status_code == 200

    inbox_page_1 = api_client.get("/inbox/tasks", params={"pageSize": 2, "sort": "priority"})
    assert inbox_page_1.status_code == 200
    first_page = inbox_page_1.json()
    assert first_page["pagination"]["total"] >= 3
    items = first_page["items"]
    assert len(items) == 2
    assert items[0]["priority"] >= items[1]["priority"]
    assert items[0]["links"]["asin"] == asin
    assert items[0]["status"] == "open"
    assert items[0]["why"]
    assert items[0]["alternatives"]

    inbox_page_2 = api_client.get("/inbox/tasks", params={"page": 2, "pageSize": 2, "sort": "priority"})
    assert inbox_page_2.status_code == 200
    second_page = inbox_page_2.json()
    assert second_page["items"]
    remaining_asins = {item["links"]["asin"] for item in second_page["items"]}
    assert asin in remaining_asins or "DECISION-003" in remaining_asins

    dismiss_id = items[0]["id"]
    dismiss_response = api_client.post(f"/inbox/tasks/{dismiss_id}/dismiss", json={"note": "handled"})
    assert dismiss_response.status_code == 200
    dismissed = dismiss_response.json()
    assert dismissed["status"] == "cancelled"
    assert dismissed["id"] == dismiss_id

    manual_lookup = api_client.get("/inbox/tasks", params={"taskId": manual_task_id})
    assert manual_lookup.status_code == 200
    manual_payload = manual_lookup.json()["items"][0]
    assert manual_payload["decision"] == "audit_pricing"
    assert manual_payload["links"]["vendor_id"] == vendor_secondary
    assert manual_payload["status"] == "open"
    assert manual_payload["why"][0]["code"] == "audit_requested"
    assert "message" in manual_payload["why"][0]


def test_roi_pagination_stable_with_ties(api_client, db_engine, allow_admin_user: UserCtx):
    _ensure_freight_rate(db_engine)
    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM events"))
        conn.execute(text("DELETE FROM tasks"))
    _seed_roi_rows(db_engine, "ROI-STABLE-1", 880, cost=10.0, buybox_price=15.0)
    _seed_roi_rows(db_engine, "ROI-STABLE-2", 881, cost=10.0, buybox_price=15.0)

    page_one = api_client.get("/roi", params={"page_size": 1, "sort": "roi_pct_desc"})
    assert page_one.status_code == 200
    first_payload = page_one.json()
    assert first_payload["pagination"]["total"] >= 2
    first_asin = first_payload["items"][0]["asin"]

    page_two = api_client.get("/roi", params={"page": 2, "page_size": 1, "sort": "roi_pct_desc"})
    assert page_two.status_code == 200
    second_payload = page_two.json()
    assert second_payload["items"]
    second_asin = second_payload["items"][0]["asin"]

    assert {first_asin, second_asin} == {"ROI-STABLE-1", "ROI-STABLE-2"}
