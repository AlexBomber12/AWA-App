from __future__ import annotations

import pytest
from asgi_correlation_id import correlation_id
from awa_common.settings import Settings
from fastapi import FastAPI
from httpx import AsyncClient

from services.api import logging_config, metrics


def test_settings_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:secret@db/app")
    s = Settings()
    assert s.ENV == "prod"
    assert s.DATABASE_URL.endswith("@db/app")


def test_settings_role_resolution_and_configured_roles() -> None:
    s = Settings(ROLE_MAP_JSON='{"admin":["admins"],"ops":["Ops"],"viewer":["viewers"]}')
    resolved = s.resolve_role_set({"admins", "random"})
    assert resolved == {"admin"}
    resolved = s.resolve_role_set({"viewer"})
    assert resolved == {"viewer"}
    assert s.configured_roles() == {"admin", "ops", "viewer"}


def test_settings_should_protect_path(monkeypatch) -> None:
    s = Settings(AUTH_REQUIRED_ROUTES_REGEX=r"^/secure")
    assert s.should_protect_path("/secure/report") is True
    assert s.should_protect_path("/public") is False


def test_settings_invalid_regex_falls_back_to_protect_all() -> None:
    s = Settings(AUTH_REQUIRED_ROUTES_REGEX="*invalid[")
    assert s.should_protect_path("/anything") is True


def test_redacted_masks_credentials() -> None:
    s = Settings(DATABASE_URL="postgresql+psycopg://user:secret@db/app")
    red = s.redacted()
    assert red["DATABASE_URL"] == "postgresql+psycopg://user:****@db/app"


@pytest.mark.asyncio
async def test_metrics_middleware_records_request() -> None:
    metrics.requests_total.clear()
    metrics.request_duration_seconds.clear()
    metrics.inprogress_requests.clear()

    app = FastAPI()
    metrics.install_metrics(app)

    @app.get("/items/{item_id}")
    async def _handler(item_id: str):
        return {"item_id": item_id}

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        resp = await client.get("/items/42")
        assert resp.status_code == 200

    collected = metrics.requests_total.collect()[0].samples
    routes = {sample.labels["route"] for sample in collected}
    assert "/items/{item_id}" in routes or "/items/42" in routes


def test_request_id_injector_adds_context() -> None:
    token = correlation_id.set("req-123")
    try:
        event = {}
        updated = logging_config._request_id_injector(None, "", event)
        assert updated["request_id"] == "req-123"
    finally:
        correlation_id.reset(token)


def test_request_id_injector_no_context() -> None:
    event = {}
    updated = logging_config._request_id_injector(None, "", event)
    assert "request_id" not in updated
