from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

from awa_common.security.request_limits import (
    BodySizeLimitMiddleware,
    _RequestTooLarge,
    install_body_size_limit,
)
from awa_common.settings import settings


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


def test_invalid_content_length_ignored(monkeypatch):
    monkeypatch.setattr(settings, "MAX_REQUEST_BYTES", 64, raising=False)
    app = _build_echo_app()
    with TestClient(app) as client:
        response = client.post(
            "/echo",
            data='{"payload":"ok"}',
            headers={
                "Content-Type": "application/json",
                "Content-Length": "not-a-number",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"payload": "ok"}


@pytest.mark.anyio
async def test_chunked_request_enforced_without_content_length():
    settings_stub = SimpleNamespace(MAX_REQUEST_BYTES=8)
    middleware = BodySizeLimitMiddleware(lambda scope, receive, send: None, settings=settings_stub)

    chunks = [b"abcd", b"efgh", b"ijkl"]

    async def receive() -> dict[str, Any]:
        if chunks:
            chunk = chunks.pop(0)
            return {"type": "http.request", "body": chunk, "more_body": bool(chunks)}
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/stream",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
        "scheme": "http",
    }
    request = StarletteRequest(scope, receive)

    async def call_next(req: StarletteRequest) -> StarletteResponse:
        await req.body()
        return StarletteResponse("ok")

    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 413
    assert json.loads(response.body.decode()) == {"detail": "Request body too large"}


@pytest.mark.anyio
async def test_body_size_limit_handles_exception_group():
    settings_stub = SimpleNamespace(MAX_REQUEST_BYTES=1)
    middleware = BodySizeLimitMiddleware(lambda scope, receive, send: None, settings=settings_stub)

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/stream",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 0),
        "server": ("test", 80),
        "scheme": "http",
    }
    request = StarletteRequest(scope, receive)

    async def call_next(req: StarletteRequest) -> StarletteResponse:
        raise BaseExceptionGroup("wrapper", [_RequestTooLarge()])

    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 413
    assert json.loads(response.body.decode()) == {"detail": "Request body too large"}
