import json
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from services.api.db import get_session
from services.worker.repricer.app import main


class StubResult:
    def __init__(self, mapping):
        self._mapping = mapping

    def mappings(self):
        return self

    def first(self):
        return self._mapping


class StubSession:
    def __init__(self, rows: dict[str, dict]):
        self.rows = rows
        self.calls: list[tuple] = []
        self.inserts: list[dict] = []
        self.committed = False

    async def execute(self, stmt, params=None):
        self.calls.append((stmt, params))
        text_stmt = str(stmt)
        if "INSERT INTO price_updates_log" in text_stmt:
            self.inserts.append(params)
            return StubResult(None)

        asin = params["asin"]
        mapping = self.rows.get(asin)
        if mapping is None:
            return StubResult(None)
        return StubResult(mapping)

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_simulate_endpoint_returns_expected_strategy():
    stub = StubSession(
        rows={
            "ASIN1234567": {
                "cost": Decimal("10"),
                "fees": Decimal("2"),
                "buybox_price": Decimal("16"),
            }
        }
    )

    async def override_session():
        yield stub

    main.app.dependency_overrides[get_session] = override_session

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/pricing/simulate", json={"asin": "ASIN1234567"})

    body = resp.json()
    assert resp.status_code == 200
    item = body["results"][0]
    assert item["strategy"] == "min_roi+buybox_gap"
    assert item["context"]["applied"] == ["min_roi", "buybox_gap"]

    main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_apply_endpoint_inserts_log_and_marks_changed():
    stub = StubSession(
        rows={
            "ASIN1234567": {
                "cost": Decimal("10"),
                "fees": Decimal("2"),
                "buybox_price": Decimal("16"),
            }
        }
    )

    async def override_session():
        yield stub

    main.app.dependency_overrides[get_session] = override_session

    transport = ASGITransport(app=main.app)
    payload = {
        "items": [
            {
                "asin": "ASIN1234567",
                "new_price": "15.68",
                "old_price": "15.00",
                "strategy": "min_roi+buybox_gap",
                "note": "audit",
            }
        ]
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/pricing/apply", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["applied"] == 1
    assert body["results"][0]["changed"] is True
    assert len(stub.inserts) == 1
    logged = stub.inserts[0]
    context = json.loads(logged["context"])
    assert context["note"] == "audit"
    assert context["applied"] == ["min_roi", "buybox_gap"]
    assert stub.committed is True

    main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_apply_endpoint_dry_run_skips_inserts():
    stub = StubSession(
        rows={
            "ASIN0000001": {
                "cost": Decimal("9"),
                "fees": Decimal("1"),
                "buybox_price": Decimal("12"),
            }
        }
    )

    async def override_session():
        yield stub

    main.app.dependency_overrides[get_session] = override_session

    payload = {
        "dry_run": True,
        "items": [
            {
                "asin": "ASIN0000001",
                "new_price": "11.76",
                "old_price": "11.76",
                "strategy": "min_roi",
            }
        ],
    }

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/pricing/apply", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["applied"] == 0
    assert body["results"][0]["changed"] is False
    assert stub.inserts == []
    assert stub.committed is False

    main.app.dependency_overrides.clear()
