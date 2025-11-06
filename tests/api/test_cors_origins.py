from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from awa_common.settings import settings
from services.api.main import install_cors


def _build_app(monkeypatch: pytest.MonkeyPatch, app_env: str, cors_origins: str | None):
    """Create a FastAPI instance with the CORS middleware configured."""
    monkeypatch.setattr(settings, "APP_ENV", app_env, raising=False)
    monkeypatch.setattr(settings, "CORS_ORIGINS", cors_origins, raising=False)

    app = FastAPI()

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    install_cors(app)
    return app


def test_dev_profile_allows_localhost_by_default(monkeypatch: pytest.MonkeyPatch):
    app = _build_app(monkeypatch, "dev", None)
    client = TestClient(app)
    allowed_origin = "http://localhost:3000"

    response = client.get("/ping", headers={"Origin": allowed_origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed_origin
    assert response.headers.get("access-control-allow-credentials") == "true"

    preflight = client.options(
        "/ping",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == allowed_origin
    assert preflight.headers.get("access-control-allow-credentials") == "true"
    allow_methods_header = preflight.headers.get("access-control-allow-methods")
    assert allow_methods_header is not None
    for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]:
        assert method in allow_methods_header

    rejected = client.get("/ping", headers={"Origin": "http://evil.test"})
    assert rejected.headers.get("access-control-allow-origin") is None


def test_prod_profile_only_permits_configured_origin(monkeypatch: pytest.MonkeyPatch):
    origin = "https://app.example.com"
    app = _build_app(monkeypatch, "prod", origin)
    client = TestClient(app)

    ok = client.get("/ping", headers={"Origin": origin})
    assert ok.headers.get("access-control-allow-origin") == origin

    preflight = client.options(
        "/ping",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
    )
    assert preflight.headers.get("access-control-allow-origin") == origin

    denied = client.get("/ping", headers={"Origin": "https://other.example.com"})
    assert denied.headers.get("access-control-allow-origin") is None


def test_stage_and_prod_require_explicit_origins(monkeypatch: pytest.MonkeyPatch):
    app = FastAPI()
    monkeypatch.setattr(settings, "APP_ENV", "prod", raising=False)
    monkeypatch.setattr(settings, "CORS_ORIGINS", None, raising=False)

    with pytest.raises(RuntimeError, match="CORS_ORIGINS must be set"):
        install_cors(app)


def test_stage_and_prod_reject_wildcard(monkeypatch: pytest.MonkeyPatch):
    app = FastAPI()
    monkeypatch.setattr(settings, "APP_ENV", "stage", raising=False)
    monkeypatch.setattr(settings, "CORS_ORIGINS", "*", raising=False)

    with pytest.raises(RuntimeError, match="Wildcard origins"):
        install_cors(app)
