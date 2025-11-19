import asyncio

import pytest

import awa_common.db as db_module


def test_build_sqlalchemy_url_uses_shared_builder(monkeypatch):
    monkeypatch.setattr(db_module, "build_dsn", lambda *args, **kwargs: "postgresql+psycopg://x")
    assert db_module.build_sqlalchemy_url() == "postgresql+psycopg://x"


def test_build_asyncpg_dsn_strips_driver(monkeypatch):
    monkeypatch.setattr(
        db_module,
        "build_dsn",
        lambda *args, **kwargs: "postgresql+psycopg://user:secret@example:5432/app",
    )
    dsn = db_module.build_asyncpg_dsn()
    assert dsn == "postgresql://user:secret@example:5432/app"


@pytest.mark.asyncio
async def test_create_pg_pool_retries_then_succeeds(monkeypatch):
    attempts = {"count": 0}

    async def fake_create_pool(*_args, **_kwargs):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("db down")
        return "pool"

    async def fake_sleep(_delay: float):
        return None

    monkeypatch.setattr(db_module, "create_pool", fake_create_pool)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    pool = await db_module.create_pg_pool()
    assert pool == "pool"
    assert attempts["count"] == 3


def test_refresh_mvs_with_connection(monkeypatch):
    executed = []

    class DummyConn:
        def execute(self, stmt):
            executed.append(str(stmt))
            return type("R", (), {"scalar": lambda self: 1})()

    conn = DummyConn()
    monkeypatch.setenv("ENABLE_LIVE", "1")
    db_module.refresh_mvs(conn)
    assert any("v_refund_totals" in stmt for stmt in executed)
    assert any("v_reimb_totals" in stmt for stmt in executed)


def test_refresh_mvs_with_engine(monkeypatch):
    captures = []

    class DummyConn:
        def execute(self, stmt):
            captures.append(str(stmt))
            return type("R", (), {"scalar": lambda self: 1})()

    class DummyContext:
        def __init__(self, conn):
            self.conn = conn

        def __enter__(self):
            return self.conn

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyEngine:
        def begin(self):
            return DummyContext(DummyConn())

    engine = DummyEngine()
    monkeypatch.setenv("ENABLE_LIVE", "0")
    monkeypatch.setattr(db_module, "Engine", (DummyEngine,))
    db_module.refresh_mvs(engine)
    assert len(captures) >= 2


def test_refresh_mvs_defaults_to_concurrent(monkeypatch):
    executed = []

    class DummyConn:
        def execute(self, stmt):
            executed.append(str(stmt))

            class R:
                def scalar(self_inner):
                    return 1

            return R()

    monkeypatch.delenv("ENABLE_LIVE", raising=False)
    from awa_common.settings import Settings

    monkeypatch.setattr(db_module, "settings", Settings())
    db_module.refresh_mvs(DummyConn())
    refreshes = [stmt for stmt in executed if "REFRESH MATERIALIZED VIEW" in stmt]
    assert refreshes and all("CONCURRENTLY" in stmt for stmt in refreshes)
