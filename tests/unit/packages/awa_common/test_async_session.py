from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import pytest

from awa_common.db import async_session as async_db


def _reset_state():
    async_db._ENGINE = None
    async_db._SESSIONMAKER = None
    async_db._POOL_WARNINGS.clear()


def teardown_module():
    _reset_state()


def test_ensure_async_driver_normalizes_postgres():
    url = async_db._ensure_async_driver("postgresql://user:pass@localhost/app")
    assert url.startswith("postgresql+asyncpg://")
    url_with_driver = async_db._ensure_async_driver("postgresql+psycopg://host/db")
    assert url_with_driver.startswith("postgresql+asyncpg://")
    assert async_db._ensure_async_driver("invalid-url") == "invalid-url"


def test_resolve_dsn_prefers_explicit_and_settings(monkeypatch):
    explicit = async_db._resolve_dsn("postgresql://u:p@h/db")
    assert explicit.startswith("postgresql+asyncpg://")
    monkeypatch.setattr(async_db, "settings", SimpleNamespace(POSTGRES_DSN="postgresql://x/db"))
    resolved = async_db._resolve_dsn(None)
    assert resolved.startswith("postgresql+asyncpg://x")


def test_resolve_dsn_handles_missing_settings(monkeypatch):
    class Broken:
        @property
        def POSTGRES_DSN(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(async_db, "settings", Broken())
    monkeypatch.setattr(async_db, "build_dsn", lambda sync=False: "postgresql://fallback/db")
    fallback = async_db._resolve_dsn(None)
    assert fallback == "postgresql://fallback/db"


def test_init_async_engine_initializes_once(monkeypatch):
    _reset_state()
    captured = {}

    def fake_create_engine(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return "engine"

    class FakeSessionFactory:
        def __init__(self, bind, **_):
            captured["engine"] = bind

        def __call__(self):
            return "session"

    monkeypatch.setattr(async_db, "create_async_engine", fake_create_engine)
    monkeypatch.setattr(async_db, "async_sessionmaker", FakeSessionFactory)
    engine = async_db.init_async_engine("postgresql://user:pass@db/app")
    assert engine == "engine"
    assert captured["url"].startswith("postgresql+asyncpg://")
    assert async_db._ENGINE == "engine"
    assert async_db._SESSIONMAKER is not None
    # second call should reuse existing engine
    reused = async_db.init_async_engine()
    assert reused == "engine"


def test_getters_initialize_when_missing(monkeypatch):
    _reset_state()

    def _fake_init(dsn=None):
        async_db._SESSIONMAKER = "factory"
        async_db._ENGINE = "engine"
        return "engine"

    monkeypatch.setattr(async_db, "init_async_engine", _fake_init)
    async_db._SESSIONMAKER = None
    result = async_db.get_sessionmaker()
    assert result is not None
    async_db._ENGINE = None
    monkeypatch.setattr(async_db, "init_async_engine", lambda dsn=None: "engine-2")
    assert async_db.get_async_engine() == "engine-2"
    async_db._ENGINE = "engine-existing"
    assert async_db.get_async_engine() == "engine-existing"


def test_pool_monitor_warns_near_capacity(monkeypatch, caplog):
    caplog.set_level("WARNING")
    usage: list[tuple[tuple, dict]] = []
    near: list[str] = []
    hooks: list[Callable[..., Any]] = []

    monkeypatch.setattr(async_db, "record_db_pool_usage", lambda *args, **kwargs: usage.append((args, kwargs)))
    monkeypatch.setattr(async_db, "record_db_pool_near_limit", lambda pool: near.append(pool))

    def fake_listens_for(_target, _event_name):
        def decorator(fn):
            hooks.append(fn)
            return fn

        return decorator

    monkeypatch.setattr(async_db.event, "listens_for", fake_listens_for)

    class FakePool:
        def __init__(self, checked: int, overflow: int = 0) -> None:
            self._checked = checked
            self._overflow = overflow

        def checkedout(self) -> int:
            return self._checked

        def overflow(self) -> int:
            return self._overflow

    pool = FakePool(checked=9, overflow=1)
    engine = SimpleNamespace(sync_engine=SimpleNamespace(pool=pool))
    async_db._POOL_WARNINGS.clear()

    async_db._install_pool_monitor(
        engine,
        pool_label="api",
        pool_size=10,
        max_overflow=0,
        warn_pct=0.5,
        warn_interval_s=0,
    )

    assert near == ["api"]
    assert any("db_pool.near_limit" in rec.message for rec in caplog.records)
    assert usage
    for hook in hooks:
        hook()


@pytest.mark.asyncio
async def test_get_async_session_rolls_back_on_error(monkeypatch):
    class DummySession:
        def __init__(self):
            self.rollback_called = False

        async def rollback(self):
            self.rollback_called = True

    class DummyContext:
        def __init__(self):
            self.session = DummySession()

        async def __aenter__(self):
            return self.session

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(async_db, "get_sessionmaker", lambda: (lambda: DummyContext()))
    gen = async_db.get_async_session()
    session = await gen.__anext__()
    assert isinstance(session, DummySession)
    with pytest.raises(RuntimeError):
        await gen.athrow(RuntimeError("boom"))
    assert session.rollback_called is True
