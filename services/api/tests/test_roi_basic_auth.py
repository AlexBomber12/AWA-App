import base64
import os
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def _auth_headers(u, p):
    token = base64.b64encode(f"{u}:{p}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@contextmanager
def _client(monkeypatch):
    monkeypatch.setenv("PG_USER", "postgres")
    monkeypatch.setenv("PG_PASSWORD", "pass")
    monkeypatch.setenv("PG_DATABASE", "awa")
    monkeypatch.setenv("PG_HOST", "localhost")
    monkeypatch.setenv("PG_PORT", "5432")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:pass@localhost:5432/awa")

    from fastapi_limiter import FastAPILimiter

    import services.api.main as main
    from services.api import db

    class _DummyRedis:
        async def evalsha(self, *args, **kwargs):  # pragma: no cover - simple stub
            return 0

    async def _noop(*args, **kwargs) -> None:  # pragma: no cover - simple stub
        return None

    async def _fake_init(redis):  # pragma: no cover - simple stub
        FastAPILimiter.redis = _DummyRedis()

    async def _fake_close():  # pragma: no cover - simple stub
        FastAPILimiter.redis = None

    monkeypatch.setattr(main, "_wait_for_db", _noop)
    monkeypatch.setattr(FastAPILimiter, "init", _fake_init)
    monkeypatch.setattr(FastAPILimiter, "close", _fake_close)

    class FakeSession:
        async def execute(self, query, params=None):  # pragma: no cover - simple stub
            class Result:
                def mappings(self):
                    class Rows:
                        def all(self):
                            return []

                    return Rows()

            return Result()

    async def fake_get_session():
        yield FakeSession()

    main.app.dependency_overrides[db.get_session] = fake_get_session
    with TestClient(main.app) as client:
        yield client
    main.app.dependency_overrides.clear()


def test_roi_needs_basic_auth(monkeypatch):
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    with _client(monkeypatch) as client:
        r = client.get("/roi")  # no auth
        assert r.status_code in (401, 403)


def test_roi_basic_auth_good(monkeypatch):
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    with _client(monkeypatch) as client:
        r = client.get("/roi", headers=_auth_headers("u", "p"))
        assert r.status_code == 200


def test_score_needs_basic_auth(monkeypatch):
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    with _client(monkeypatch) as client:
        r = client.post("/score", json={"asins": ["A1"]})  # no auth
        assert r.status_code in (401, 403)


def test_stats_contract_needs_basic_auth(monkeypatch):
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    with _client(monkeypatch) as client:
        r = client.get("/stats/kpi")
        assert r.status_code in (401, 403)
