from __future__ import annotations

from awa_common.security.request_limits import install_body_size_limit
from awa_common.settings import settings
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


def _build_echo_app() -> FastAPI:
    app = FastAPI()
    install_body_size_limit(app, settings)

    @app.post("/echo")
    async def echo(payload: dict[str, str]) -> dict[str, str]:
        return payload

    @app.post("/stream")
    async def stream(request: Request) -> dict[str, int]:
        data = await request.body()
        return {"size": len(data)}

    return app


def test_request_under_limit_allowed(monkeypatch):
    monkeypatch.setattr(settings, "MAX_REQUEST_BYTES", 64, raising=False)
    app = _build_echo_app()
    with TestClient(app) as client:
        payload = {"data": "ok"}
        response = client.post("/echo", json=payload)
        assert response.status_code == 200
        assert response.json() == payload


def test_request_over_limit_rejected(monkeypatch):
    monkeypatch.setattr(settings, "MAX_REQUEST_BYTES", 32, raising=False)
    app = _build_echo_app()
    with TestClient(app) as client:
        payload = {"data": "x" * 48}
        response = client.post("/echo", json=payload)
        assert response.status_code == 413
        assert response.json() == {"detail": "Request body too large"}


def test_chunked_request_enforced(monkeypatch):
    monkeypatch.setattr(settings, "MAX_REQUEST_BYTES", 16, raising=False)
    app = _build_echo_app()
    with TestClient(app) as client:

        def payload():
            for _ in range(3):
                yield b"1234567890"

        response = client.post("/stream", data=payload())
        assert response.status_code == 413
        assert response.json() == {"detail": "Request body too large"}
