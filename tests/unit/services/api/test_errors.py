import json
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse

import services.api.errors as errors


class DummyLogger:
    def __init__(self):
        self.records: list[tuple[str, dict[str, Any]]] = []

    def info(self, event: str, **kwargs):
        self.records.append((event, kwargs))

    def warning(self, event: str, **kwargs):
        self.records.append((event, kwargs))

    def error(self, event: str, **kwargs):
        self.records.append((event, kwargs))

    def exception(self, event: str, **kwargs):
        self.records.append((event, kwargs))


def _make_request(app: FastAPI) -> Request:
    scope = {
        "type": "http",
        "app": app,
        "path": "/test",
        "headers": [(b"x-request-id", b"req-123")],
        "method": "GET",
    }
    return StarletteRequest(scope, receive=lambda: None)


@pytest.fixture
def dummy_logger(monkeypatch):
    logger = DummyLogger()
    monkeypatch.setattr(errors.structlog, "get_logger", lambda *args, **kwargs: logger)
    return logger


@pytest.fixture
def app_with_handlers(monkeypatch):
    app = FastAPI()
    monkeypatch.setattr(
        errors, "correlation_id", SimpleNamespace(get=lambda: "req-123")
    )
    errors.install_exception_handlers(app)
    return app


@pytest.mark.asyncio
async def test_validation_error_handler_returns_details(
    app_with_handlers, dummy_logger
):
    request = _make_request(app_with_handlers)
    handler = app_with_handlers.exception_handlers[RequestValidationError]
    exc = RequestValidationError([{"loc": ("body", "field"), "msg": "invalid"}])
    response: JSONResponse = await handler(request, exc)
    assert response.status_code == 422
    body = json.loads(response.body)
    assert body["error"]["request_id"] == "req-123"
    assert dummy_logger.records[0][0] == "validation_error"


@pytest.mark.asyncio
async def test_http_exception_handler_handles_rate_limit(
    app_with_handlers, dummy_logger
):
    request = _make_request(app_with_handlers)
    handler = app_with_handlers.exception_handlers[StarletteHTTPException]
    exc = HTTPException(status_code=429, detail="slow down")
    response = await handler(request, exc)
    assert response.status_code == 429
    body = json.loads(response.body)
    assert body["error"]["type"] == "rate_limited"
    assert dummy_logger.records[-1][0] == "rate_limited"


@pytest.mark.asyncio
async def test_http_exception_handler_handles_other_errors(
    app_with_handlers, dummy_logger
):
    request = _make_request(app_with_handlers)
    handler = app_with_handlers.exception_handlers[StarletteHTTPException]
    exc = HTTPException(status_code=404, detail="missing")
    response = await handler(request, exc)
    assert response.status_code == 404
    body = json.loads(response.body)
    assert body["error"]["message"] == "missing"
    assert dummy_logger.records[-1][0] == "http_error"


@pytest.mark.asyncio
async def test_db_exception_handler_returns_500(app_with_handlers, dummy_logger):
    request = _make_request(app_with_handlers)
    handler = app_with_handlers.exception_handlers[errors.psycopg.Error]

    class DummyError(errors.psycopg.Error):
        pgcode = "08006"

    response = await handler(request, DummyError())
    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["error"]["type"] == "db_unavailable"
    assert dummy_logger.records[-1][0] == "db_error"


@pytest.mark.asyncio
async def test_unhandled_exception_handler_captures_sentry(
    app_with_handlers, dummy_logger, monkeypatch
):
    captured = {}

    def fake_capture(exc):
        captured["exc"] = exc

    monkeypatch.setattr(errors.sentry_sdk, "capture_exception", fake_capture)
    request = _make_request(app_with_handlers)
    handler = app_with_handlers.exception_handlers[Exception]
    response = await handler(request, RuntimeError("boom"))
    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["error"]["type"] == "internal_error"
    assert isinstance(captured["exc"], RuntimeError)
    assert dummy_logger.records[-1][0] == "unhandled_error"
