from __future__ import annotations

import httpx
import pytest


@pytest.mark.anyio
async def test_bulk_persists_rows_and_closes_client(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.fees_h10 import worker

    rows = []
    closed = {"count": 0}
    disposed = {"count": 0}

    async def fake_fetch(asin: str) -> dict[str, object]:
        if asin == "FAIL":
            raise httpx.TimeoutException("boom", request=httpx.Request("GET", "https://example.com"))
        return {"asin": asin, "marketplace": "US", "fee_type": "fba", "amount": 1.0}

    class DummyEngine:
        def dispose(self) -> None:
            disposed["count"] += 1

    def fake_create_engine(_url: str, *, future: bool):
        return DummyEngine()

    def fake_upsert(engine, payload, *, testing: bool):
        rows.extend(payload)
        return {"inserted": len(payload)}

    async def fake_close() -> None:
        closed["count"] += 1

    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/db")
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setattr(worker, "fetch_fees", fake_fetch, raising=False)
    monkeypatch.setattr(worker, "create_engine", fake_create_engine, raising=False)
    monkeypatch.setattr(worker.repo, "upsert_fees_raw", fake_upsert, raising=False)
    monkeypatch.setattr(worker, "close_http_client", fake_close, raising=False)

    await worker._bulk(["OK", "FAIL"])

    assert rows == [{"asin": "OK", "marketplace": "US", "fee_type": "fba", "amount": 1.0}]
    assert closed["count"] == 1
    assert disposed["count"] == 1


@pytest.mark.anyio
async def test_bulk_returns_early_without_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.fees_h10 import worker

    called = {"repo": 0, "engine": 0, "closed": 0}

    async def fake_fetch(asin: str) -> dict[str, object]:
        return {"asin": asin, "marketplace": "US", "fee_type": "fba", "amount": 1.0}

    def fake_create_engine(*_args, **_kwargs):
        called["engine"] += 1
        return object()

    def fake_upsert(*_args, **_kwargs):
        called["repo"] += 1

    async def fake_close() -> None:
        called["closed"] += 1

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(worker, "fetch_fees", fake_fetch, raising=False)
    monkeypatch.setattr(worker, "create_engine", fake_create_engine, raising=False)
    monkeypatch.setattr(worker.repo, "upsert_fees_raw", fake_upsert, raising=False)
    monkeypatch.setattr(worker, "close_http_client", fake_close, raising=False)

    await worker._bulk(["ONLY"])

    assert called["repo"] == 0
    assert called["engine"] == 0
    assert called["closed"] == 1


@pytest.mark.anyio
async def test_bulk_returns_when_no_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.fees_h10 import worker

    called = {"engine": 0, "closed": 0}

    async def fake_fetch(_asin: str) -> dict[str, object]:
        raise ValueError("bad data")

    def fake_create_engine(*_args, **_kwargs):
        called["engine"] += 1
        return object()

    async def fake_close() -> None:
        called["closed"] += 1

    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost/db")
    monkeypatch.setattr(worker, "fetch_fees", fake_fetch, raising=False)
    monkeypatch.setattr(worker, "create_engine", fake_create_engine, raising=False)
    monkeypatch.setattr(worker, "close_http_client", fake_close, raising=False)

    await worker._bulk(["ONLY"])

    assert called["engine"] == 0
    assert called["closed"] == 1
