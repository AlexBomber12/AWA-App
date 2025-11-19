from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport

from awa_common import roi_views
from awa_common.security.models import Role
from services.api import security
from services.api.main import app

pytestmark = pytest.mark.integration


@pytest.fixture
async def async_api_client():
    transport = ASGITransport(app=app, lifespan="on")
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def allow_ops_user(fastapi_dep_overrides, dummy_user_ctx):
    user = dummy_user_ctx(roles=[Role.ops])

    async def _viewer():
        return user

    async def _ops():
        return user

    def _limit_provider():
        async def _noop(_request):
            return None

        return _noop

    with fastapi_dep_overrides(
        app,
        **{
            security.require_viewer: _viewer,
            security.require_ops: _ops,
            security.limit_viewer: _limit_provider,
            security.limit_ops: _limit_provider,
        },
    ):
        yield user


async def _seed_roi_tables(pg_pool):
    async with pg_pool.acquire() as conn:  # type: ignore[attr-defined]
        await conn.execute("DELETE FROM vendor_prices")
        await conn.execute("DELETE FROM keepa_offers")
        await conn.execute("DELETE FROM fees_raw")
        await conn.execute("DELETE FROM freight_rates")
        await conn.execute("DELETE FROM offers")
        await conn.execute("DELETE FROM products")
        await conn.execute(
            """
            INSERT INTO products(asin, title, category, weight_kg, status)
            VALUES
                ('A1','t1','cat',1,'pending'),
                ('A2','t2','cat',1,'pending')
            ON CONFLICT (asin) DO UPDATE SET title=EXCLUDED.title,
                                            category=EXCLUDED.category,
                                            weight_kg=EXCLUDED.weight_kg,
                                            status=EXCLUDED.status
            """
        )
        await conn.execute(
            """
            INSERT INTO vendors(id, name) VALUES (1,'ACME GmbH')
            ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name
            """
        )
        await conn.execute(
            """
            INSERT INTO vendor_prices(vendor_id, sku, cost)
            VALUES (1,'A1',10),(1,'A2',25)
            ON CONFLICT (vendor_id, sku) DO UPDATE SET cost=EXCLUDED.cost
            """
        )
        await conn.execute(
            """
            INSERT INTO freight_rates(lane, mode, eur_per_kg)
            VALUES ('EU→IT','sea',1)
            ON CONFLICT (lane, mode) DO UPDATE SET eur_per_kg=EXCLUDED.eur_per_kg
            """
        )
        await conn.execute(
            """
            INSERT INTO fees_raw(asin, fulfil_fee, referral_fee, storage_fee, currency)
            VALUES ('A1',1,1,1,'EUR'), ('A2',1,1,1,'EUR')
            ON CONFLICT (asin) DO UPDATE SET updated_at=CURRENT_TIMESTAMP
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS test_roi_view(
                asin text primary key,
                roi_pct numeric
            )
            """
        )
        await conn.execute("TRUNCATE test_roi_view")
        await conn.execute("INSERT INTO test_roi_view(asin, roi_pct) VALUES ('A1', 50), ('A2', 10)")


def _set_roi_view(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    roi_views.clear_caches()
    monkeypatch.setattr(roi_views.settings, "ROI_VIEW_NAME", name, raising=False)
    roi_views.current_roi_view(ttl_seconds=0)


@pytest.mark.asyncio
async def test_roi_review_async_filters(monkeypatch, pg_pool, async_api_client, allow_ops_user):
    _set_roi_view(monkeypatch, "test_roi_view")
    await _seed_roi_tables(pg_pool)

    patched = {"called": False}

    def _boom(*_args, **_kwargs):
        patched["called"] = True
        raise AssertionError("sync engine should not be used")

    monkeypatch.setattr("sqlalchemy.create_engine", _boom)

    response = await async_api_client.get("/roi-review?roi_min=20")
    assert response.status_code == 200
    assert "A1" in response.text and "A2" not in response.text
    assert patched["called"] is False


@pytest.mark.asyncio
async def test_roi_review_bulk_approve(monkeypatch, pg_pool, async_api_client, allow_ops_user):
    _set_roi_view(monkeypatch, "test_roi_view")
    await _seed_roi_tables(pg_pool)

    payload = {"asins": ["A1", "A2"]}
    response = await async_api_client.post("/roi-review/approve", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert sorted(body["approved_ids"]) == ["A1", "A2"]
    assert body["updated"] == 2

    async with pg_pool.acquire() as conn:  # type: ignore[attr-defined]
        rows = await conn.fetch("SELECT asin, status FROM products ORDER BY asin")
    statuses = {row["asin"]: row["status"] for row in rows}
    assert statuses == {"A1": "approved", "A2": "approved"}
