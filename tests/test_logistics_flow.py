import pytest

from services.logistics_etl import client, flow, repository


@pytest.mark.asyncio
async def test_logistics_flow_dry_run(monkeypatch):
    async def fake_fetch():
        return [{"lane": "CN->DE", "mode": "sea", "eur_per_kg": 1.5}]

    called = False

    async def fake_upsert(rows):
        nonlocal called
        called = True

    monkeypatch.setattr(client, "fetch_rates", fake_fetch)
    monkeypatch.setattr(repository, "upsert_many", fake_upsert)

    rows = await flow.full(dry_run=True)
    assert rows and rows[0]["lane"] == "CN->DE"
    assert called is False
