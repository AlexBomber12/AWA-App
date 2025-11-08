from __future__ import annotations

import pytest


class _DummyAcquire:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummyConnection:
    def __init__(self, responses: list[list[dict[str, bool]]]):
        self.responses = responses
        self.queries: list[str] = []

    async def fetch(self, query: str, *params):
        self.queries.append(query)
        return self.responses.pop(0)


class _DummyPool:
    def __init__(self, conn: _DummyConnection):
        self.conn = conn
        self.closed = False

    def acquire(self):
        return _DummyAcquire(self.conn)

    async def close(self):
        self.closed = True


@pytest.mark.anyio
async def test_init_pool_creates_once(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.fees_h10 import db_async

    dummy_pool = _DummyPool(_DummyConnection([]))

    async def fake_create_pool(**kwargs):
        return dummy_pool

    monkeypatch.setattr(db_async, "_POOL", None, raising=False)
    monkeypatch.setattr(db_async.asyncpg, "create_pool", fake_create_pool, raising=False)

    pool = await db_async.init_pool()
    assert pool is dummy_pool

    # second call should reuse without invoking asyncpg again
    pool_again = await db_async.init_pool()
    assert pool_again is dummy_pool


@pytest.mark.anyio
async def test_close_pool_resets_state(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.fees_h10 import db_async

    pool = _DummyPool(_DummyConnection([]))
    monkeypatch.setattr(db_async, "_POOL", pool, raising=False)

    await db_async.close_pool()

    assert pool.closed is True
    assert db_async._POOL is None  # type: ignore[attr-defined]


@pytest.mark.anyio
async def test_upsert_fee_rows_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.fees_h10 import db_async

    conn = _DummyConnection(
        [
            [{"inserted_flag": True}],
            [{"inserted_flag": False}],
        ]
    )
    pool = _DummyPool(conn)
    monkeypatch.setattr(db_async, "_POOL", pool, raising=False)

    rows = [
        {"asin": "A1", "fulfil_fee": 1.0, "referral_fee": 1.0, "storage_fee": 0.2, "currency": "EUR"},
        {"asin": "A2", "fulfil_fee": 2.0, "referral_fee": 1.5, "storage_fee": 0.5, "currency": "USD"},
    ]

    summary = await db_async.upsert_fee_rows(rows, batch_size=1)

    assert summary == {"inserted": 1, "updated": 1}
    assert len(conn.queries) == 2
