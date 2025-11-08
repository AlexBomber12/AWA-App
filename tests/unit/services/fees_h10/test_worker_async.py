from __future__ import annotations

import asyncio

import httpx
import pytest


@pytest.mark.anyio
async def test_run_refresh_persists_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.fees_h10 import worker

    rows = []
    closed = {"count": 0}

    async def fake_fetch(asin: str) -> dict[str, object]:
        if asin == "FAIL":
            raise httpx.TimeoutException("boom", request=httpx.Request("GET", "https://example.com"))
        return {"asin": asin, "fulfil_fee": 1.0, "referral_fee": 0.5, "storage_fee": 0.2, "currency": "EUR"}

    async def fake_init():
        return None

    async def fake_close():
        closed["count"] += 1

    async def fake_upsert(payload):
        rows.extend(payload)
        return {"inserted": len(payload), "updated": 0}

    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/db")
    monkeypatch.setattr(worker, "fetch_fees", fake_fetch, raising=False)
    monkeypatch.setattr(worker.http_client, "init_http", fake_init, raising=False)
    monkeypatch.setattr(worker.http_client, "close_http", fake_close, raising=False)
    monkeypatch.setattr(worker.db_async, "upsert_fee_rows", fake_upsert, raising=False)
    monkeypatch.setattr(worker.db_async, "close_pool", fake_close, raising=False)

    await worker._run_refresh(["OK", "FAIL"])

    assert rows and rows[0]["asin"] == "OK"
    assert closed["count"] == 2  # http + db


@pytest.mark.anyio
async def test_run_refresh_skips_without_database(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.fees_h10 import worker

    called = {"db": 0}

    async def fake_fetch(asin: str) -> dict[str, object]:
        return {"asin": asin, "fulfil_fee": 1, "referral_fee": 1, "storage_fee": 0, "currency": "EUR"}

    async def fake_init():
        return None

    async def fake_close():
        return None

    async def fake_upsert(_rows):
        called["db"] += 1
        return {"inserted": 0, "updated": 0}

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(worker, "_database_configured", lambda: False, raising=False)
    monkeypatch.setattr(worker, "fetch_fees", fake_fetch, raising=False)
    monkeypatch.setattr(worker.http_client, "init_http", fake_init, raising=False)
    monkeypatch.setattr(worker.http_client, "close_http", fake_close, raising=False)
    monkeypatch.setattr(worker.db_async, "upsert_fee_rows", fake_upsert, raising=False)
    monkeypatch.setattr(worker.db_async, "close_pool", fake_close, raising=False)

    await worker._run_refresh(["ONLY"])

    assert called["db"] == 0


@pytest.mark.anyio
async def test_fetch_single_limits_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.fees_h10 import worker

    running = {"count": 0, "max": 0}

    async def fake_fetch(asin: str) -> dict[str, object]:
        running["count"] += 1
        running["max"] = max(running["max"], running["count"])
        await asyncio.sleep(0.01)
        running["count"] -= 1
        return {"asin": asin, "fulfil_fee": 1, "referral_fee": 1, "storage_fee": 0, "currency": "EUR"}

    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/db")
    monkeypatch.setattr(worker, "fetch_fees", fake_fetch, raising=False)

    async def fake_upsert(rows):
        return {"inserted": len(rows), "updated": 0}

    async def fake_init():
        return None

    async def fake_close():
        return None

    monkeypatch.setattr(worker.db_async, "upsert_fee_rows", fake_upsert, raising=False)
    monkeypatch.setattr(worker.http_client, "init_http", fake_init, raising=False)
    monkeypatch.setattr(worker.http_client, "close_http", fake_close, raising=False)
    monkeypatch.setattr(worker.db_async, "close_pool", fake_close, raising=False)
    monkeypatch.setattr(worker.SETTINGS, "H10_MAX_CONCURRENCY", 2, raising=False)

    await worker._run_refresh(["A1", "A2", "A3", "A4"])

    assert running["max"] <= worker.SETTINGS.H10_MAX_CONCURRENCY


def test_fallback_async_to_sync_executes_event_loop() -> None:
    from services.fees_h10 import worker

    async def sample() -> str:
        await asyncio.sleep(0)
        return "ok"

    sync_fn = worker._fallback_async_to_sync(sample)
    assert sync_fn() == "ok"
