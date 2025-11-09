from __future__ import annotations

from types import SimpleNamespace

import pytest

from awa_common.db import async_session as async_db


def _reset_state():
    async_db._ENGINE = None
    async_db._SESSIONMAKER = None


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
