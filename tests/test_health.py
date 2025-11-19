import pytest
from fastapi.testclient import TestClient

from services.api import db, main

pytestmark = pytest.mark.slow


def _patch_startup(monkeypatch):
    async def _noop(*_args, **_kwargs):
        return None

    class DummyRedis:
        async def ping(self):
            return "PONG"

    class DummyLimiter:
        redis = None

        @staticmethod
        async def init(redis_client):
            DummyLimiter.redis = redis_client

        @staticmethod
        async def close():
            return None

    async def _fake_wait_for_redis(*_args, **_kwargs):
        return DummyRedis()

    monkeypatch.setattr(main.settings, "STATS_ENABLE_CACHE", False, raising=False)
    monkeypatch.setattr(main, "_wait_for_db", _noop)
    monkeypatch.setattr(main, "_wait_for_redis", _fake_wait_for_redis)
    monkeypatch.setattr(main, "_check_llm", _noop)
    monkeypatch.setattr(main, "FastAPILimiter", DummyLimiter)


@pytest.mark.slow
@pytest.mark.timeout(0)
@pytest.mark.parametrize("_", range(5))
def test_health(monkeypatch, _):
    _patch_startup(monkeypatch)

    class FakeSession:
        async def execute(self, query):
            class R:
                def scalar(self):
                    from datetime import UTC, datetime

                    return datetime.now(UTC)

            return R()

    async def fake_get_session():
        yield FakeSession()

    main.app.dependency_overrides[db.get_session] = fake_get_session
    with TestClient(main.app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
    main.app.dependency_overrides.clear()
