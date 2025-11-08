from __future__ import annotations

import asyncio

import httpx
import pytest
from sqlalchemy import text

respx = pytest.importorskip("respx")


@pytest.mark.integration
@pytest.mark.anyio
@respx.mock
async def test_async_concurrency_limits(monkeypatch: pytest.MonkeyPatch, pg_engine) -> None:
    from services.fees_h10 import worker

    monkeypatch.setenv("HELIUM10_KEY", "test-key")
    monkeypatch.setattr(worker.SETTINGS, "H10_MAX_CONCURRENCY", 3, raising=False)

    with pg_engine.begin() as conn:
        conn.execute(text("TRUNCATE fees_raw;"))

    concurrency = {"current": 0, "max": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        concurrency["current"] += 1
        concurrency["max"] = max(concurrency["max"], concurrency["current"])
        await asyncio.sleep(0.05)
        concurrency["current"] -= 1
        return httpx.Response(
            200,
            json={
                "fulfillmentFee": 1.0,
                "referralFee": 0.5,
                "storageFee": 0.1,
                "currency": "EUR",
            },
        )

    respx.route(method="GET", url__regex=r"https://api\.helium10\.com/financials/fba-fees/.*").mock(side_effect=handler)

    asins = [f"ASIN{i}" for i in range(8)]
    await worker._run_refresh(asins)

    assert concurrency["max"] <= worker.SETTINGS.H10_MAX_CONCURRENCY

    with pg_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM fees_raw WHERE asin LIKE 'ASIN%'")).scalar_one()
    assert count == len(asins)

    with pg_engine.begin() as conn:
        conn.execute(text("TRUNCATE fees_raw;"))
