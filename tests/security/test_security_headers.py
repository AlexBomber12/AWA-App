from __future__ import annotations

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from awa_common.security.headers import install_security_headers
from awa_common.settings import settings


def _build_app() -> FastAPI:
    app = FastAPI()
    install_security_headers(app, settings)

    @app.get("/sample")
    def sample() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_security_headers_default():
    app = _build_app()
    with TestClient(app) as client:
        for path in ("/sample", "/ready"):
            response = client.get(path)
            assert response.status_code == 200
            headers = response.headers
            assert headers["X-Content-Type-Options"] == settings.SECURITY_X_CONTENT_TYPE_OPTIONS
            assert headers["X-Frame-Options"] == settings.SECURITY_FRAME_OPTIONS
            assert headers["Referrer-Policy"] == settings.SECURITY_REFERRER_POLICY
            assert "Strict-Transport-Security" not in headers


def test_hsts_only_in_stage_or_prod(monkeypatch):
    monkeypatch.setattr(settings, "SECURITY_HSTS_ENABLED", True, raising=False)

    monkeypatch.setattr(settings, "ENV", "stage", raising=False)
    stage_app = _build_app()
    with TestClient(stage_app) as client:
        response = client.get("/sample")
        assert response.headers.get("Strict-Transport-Security") == ("max-age=31536000; includeSubDomains; preload")

    monkeypatch.setattr(settings, "ENV", "local", raising=False)
    local_app = _build_app()
    with TestClient(local_app) as client:
        response = client.get("/sample")
        assert "Strict-Transport-Security" not in response.headers


def test_existing_header_preserved(monkeypatch):
    monkeypatch.setattr(settings, "SECURITY_HSTS_ENABLED", False, raising=False)

    app = FastAPI()
    install_security_headers(app, settings)

    @app.get("/custom")
    def custom() -> Response:
        response = Response(content="ok")
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    with TestClient(app) as client:
        response = client.get("/custom")
        assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert response.headers["Referrer-Policy"] == "no-referrer"
