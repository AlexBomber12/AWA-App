import asyncio
import types

import pytest
import sqlalchemy

import services.api.main as main
from tests.fakes import FakeRedis
from tests.unit.conftest import _StubResult


@pytest.mark.asyncio
async def test_ready_endpoint_returns_env(api_client):
    resp = await api_client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["env"] == "test"


@pytest.mark.asyncio
async def test_ready_db_success(monkeypatch, fake_db_session):
    session = fake_db_session(_StubResult(scalar="head"))

    class DummyScript:
        def get_current_head(self):
            return "head"

    monkeypatch.setattr(main, "Config", lambda path: types.SimpleNamespace())
    monkeypatch.setattr(main.ScriptDirectory, "from_config", lambda *args, **kwargs: DummyScript())
    result = await main.ready_db(session=session)
    assert result["status"] == "ready"


@pytest.mark.asyncio
async def test_ready_db_pending(monkeypatch, fake_db_session):
    session = fake_db_session(_StubResult(scalar="old"))

    class DummyScript:
        def get_current_head(self):
            return "head"

    monkeypatch.setattr(main.ScriptDirectory, "from_config", lambda *args, **kwargs: DummyScript())
    monkeypatch.setattr(main, "Config", lambda path: types.SimpleNamespace())
    with pytest.raises(main.HTTPException) as excinfo:
        await main.ready_db(session=session)
    assert excinfo.value.status_code == 503


@pytest.mark.needs_wait_for_db
@pytest.mark.asyncio
async def test_wait_for_db_retries_then_succeeds(monkeypatch):
    attempts = {"count": 0}
    monkeypatch.setenv("ENV", "local")
    main.settings.ENV = "local"

    class DummyConn:
        def __init__(self, succeed_on):
            self.succeed_on = succeed_on

        def __enter__(self):
            attempts["count"] += 1
            if attempts["count"] < self.succeed_on:
                raise RuntimeError("db down")
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, stmt):
            return None

    class DummyEngine:
        def __init__(self):
            self.conn = DummyConn(2)
            self.disposed = False

        def connect(self):
            return self.conn

        def dispose(self):
            self.disposed = True

    monkeypatch.setattr(sqlalchemy, "create_engine", lambda url: DummyEngine())

    async def fake_sleep(_delay):
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    await main._wait_for_db()
    assert attempts["count"] == 2


@pytest.mark.asyncio
async def test_wait_for_redis_retries(monkeypatch):
    attempts = {"count": 0}

    class DummyRedis:
        async def ping(self):
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise RuntimeError("redis down")
            return "PONG"

    def fake_from_url(url, *args, **kwargs):
        return DummyRedis()

    monkeypatch.setattr(main.aioredis, "from_url", fake_from_url)

    async def fake_sleep(_delay):
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    client = await main._wait_for_redis("redis://localhost")
    assert isinstance(client, DummyRedis)


@pytest.mark.asyncio
async def test_check_llm_sets_fallback(monkeypatch):
    called = {}

    class DummyResponse:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url):
            called["url"] = url
            raise RuntimeError("unreachable")

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return DummyResponse()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setenv("LLM_PROVIDER", "lan")
    monkeypatch.setenv("LLM_PROVIDER_FALLBACK", "stub")
    monkeypatch.setattr(main.httpx, "AsyncClient", DummyClient)
    await main._check_llm()
    assert main.os.getenv("LLM_PROVIDER") == "stub"


@pytest.mark.asyncio
async def test_lifespan_initialises_and_closes(monkeypatch):
    flags = {"db": 0, "redis": 0, "closed": False}

    async def fake_wait_for_db():
        flags["db"] += 1

    async def fake_wait_for_redis(url):
        flags["redis"] += 1
        return types.SimpleNamespace(ping=lambda: None)

    async def fake_check_llm():
        return None

    class DummyLimiter:
        redis = FakeRedis()

        @staticmethod
        async def init(redis_client):
            DummyLimiter.redis = redis_client

        @staticmethod
        async def close():
            flags["closed"] = True

    monkeypatch.setattr(main, "FastAPILimiter", DummyLimiter)
    monkeypatch.setattr(main, "_wait_for_db", fake_wait_for_db)
    monkeypatch.setattr(main, "_wait_for_redis", fake_wait_for_redis)
    monkeypatch.setattr(main, "_check_llm", fake_check_llm)

    async with main.lifespan(main.app):
        pass

    assert flags["db"] == 1
    assert flags["redis"] == 1
    assert flags["closed"] is True
