from fastapi.testclient import TestClient

from services.api import db, main
from services.api.main import app


class FakeSession:
    async def execute(self, query):
        class R:
            def scalar(self):
                from datetime import UTC, datetime

                return datetime.now(UTC)

        return R()


async def fake_get_session():
    yield FakeSession()


def test_health_endpoint(monkeypatch):
    app.dependency_overrides[db.get_session] = fake_get_session
    monkeypatch.setenv("STATS_ENABLE_CACHE", "0")
    monkeypatch.setattr(main.settings, "STATS_ENABLE_CACHE", False, raising=False)

    async def _noop(*_args, **_kwargs):
        return None

    async def _ping_cache(*_args, **_kwargs):
        return True

    monkeypatch.setattr("services.api.main._wait_for_db", _noop)
    monkeypatch.setattr("services.api.main._wait_for_redis", _noop)
    monkeypatch.setattr("services.api.main.configure_cache_backend", _noop)
    monkeypatch.setattr("services.api.main.close_cache", _noop)
    monkeypatch.setattr("services.api.main.ping_cache", _ping_cache)
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
    app.dependency_overrides.clear()
