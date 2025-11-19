import importlib

from fastapi.testclient import TestClient


def _get_app(monkeypatch, **env):
    env.setdefault("LLM_PROVIDER", "stub")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import services.api.main as main

    importlib.reload(main)

    async def _noop() -> None:  # pragma: no cover
        return None

    monkeypatch.setattr(main, "_wait_for_db", _noop)
    monkeypatch.setattr(main, "_wait_for_redis", _noop)

    from services.api import db as api_db

    class FakeSession:
        async def execute(self, query):  # pragma: no cover - simple stub
            class R:
                def scalar(self):
                    from datetime import UTC, datetime

                    return datetime.now(UTC)

            return R()

    async def fake_get_session():
        yield FakeSession()

    main.app.dependency_overrides[api_db.get_session] = fake_get_session

    async def _fake_init(_redis):
        return None

    async def _fake_close():
        return None

    monkeypatch.setattr(main.FastAPILimiter, "init", _fake_init)
    monkeypatch.setattr(main.FastAPILimiter, "close", _fake_close)
    return main.app


def test_cors_preflight_allowed(monkeypatch):
    app = _get_app(monkeypatch, CORS_ORIGINS="http://localhost:3000,http://web:3000")
    with TestClient(app) as client:
        r = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert r.status_code in (200, 204)
        assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert "access-control-allow-methods" in r.headers


def test_cors_simple_get_allowed(monkeypatch):
    app = _get_app(monkeypatch, CORS_ORIGINS="http://localhost:3000")
    with TestClient(app) as client:
        r = client.get("/health", headers={"Origin": "http://localhost:3000"})
        assert r.status_code == 200
        assert r.json().get("status") == "ok"
        assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_disallowed_origin(monkeypatch):
    app = _get_app(monkeypatch, CORS_ORIGINS="http://localhost:3000")
    with TestClient(app) as client:
        r = client.options(
            "/health",
            headers={
                "Origin": "http://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert r.status_code in (200, 204, 400)
        assert "access-control-allow-origin" not in r.headers
