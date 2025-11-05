from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import AsyncIterator, Callable

import pytest
from fastapi import Depends
from starlette.responses import Response

from services.api.db import get_session
from services.api.routes import roi as roi_module
from services.api.routes import score as score_module
from services.api.routes import stats as stats_module
from services.api.security import Principal, get_principal, require_admin
from tests.unit.conftest import _StubResult


def _set_override(app, dependency: Callable[..., object], override: Callable[..., object]) -> None:
    app.dependency_overrides[dependency] = override


def _clear_override(app, dependency: Callable[..., object]) -> None:
    app.dependency_overrides.pop(dependency, None)


def _protect_all(settings_obj) -> None:
    settings_obj.AUTH_REQUIRED_ROUTES_REGEX = ".*"
    settings_obj.AUTH_MODE = "forward-auth"
    settings_obj._role_regex_cache = None
    settings_obj._role_regex_cache_key = None


@pytest.mark.asyncio
async def test_ready_and_health_endpoints(api_app, api_client, fake_db_session) -> None:
    now = datetime.now(UTC)
    session = fake_db_session(_StubResult(scalar=now))

    async def _session_override() -> AsyncIterator[object]:
        yield session

    _set_override(api_app, get_session, _session_override)
    try:
        ready = await api_client.get("/ready")
        assert ready.status_code == 200
        assert ready.json()["status"] == "ok"

        health = await api_client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
    finally:
        _clear_override(api_app, get_session)


@pytest.mark.asyncio
async def test_unknown_route_returns_404(api_client) -> None:
    resp = await api_client.get("/does-not-exist")
    assert resp.status_code == 404


def _viewer_principal():
    async def _provider() -> Principal:
        return Principal(id="viewer", email="viewer@example.com", roles={"viewer"})

    return _provider


def _ops_principal():
    async def _provider() -> Principal:
        return Principal(id="ops", email="ops@example.com", roles={"ops"})

    return _provider


def _admin_principal():
    async def _provider() -> Principal:
        return Principal(id="admin", email="admin@example.com", roles={"admin"})

    return _provider


@pytest.mark.asyncio
async def test_sku_viewer_access(api_app, api_client, fake_db_session, settings_env) -> None:
    _protect_all(settings_env)
    session = fake_db_session(
        _StubResult(mappings=[{"title": "Widget", "roi_pct": 1.75, "fees": 2.5}]),
        _StubResult(
            mappings=[{"date": datetime(2024, 1, 1, tzinfo=UTC), "price": "12.34"}],
        ),
    )

    async def _session_override() -> AsyncIterator[object]:
        yield session

    _set_override(api_app, get_session, _session_override)
    _set_override(api_app, get_principal, _viewer_principal())
    try:
        resp = await api_client.get("/sku/ABC123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Widget"
        assert data["roi"] == pytest.approx(1.75)
        assert data["chartData"][0]["price"] == pytest.approx(12.34)
    finally:
        _clear_override(api_app, get_session)
        _clear_override(api_app, get_principal)


@pytest.mark.asyncio
async def test_sku_requires_viewer_role(api_app, api_client, fake_db_session, settings_env) -> None:
    _protect_all(settings_env)
    session = fake_db_session()

    async def _session_override() -> AsyncIterator[object]:
        yield session

    _set_override(api_app, get_session, _session_override)
    _set_override(api_app, get_principal, _ops_principal())
    try:
        resp = await api_client.get("/sku/NOPE123")
        assert resp.status_code == 403
    finally:
        _clear_override(api_app, get_session)
        _clear_override(api_app, get_principal)


@pytest.mark.asyncio
async def test_ingest_requires_ops_role(api_app, api_client, monkeypatch, settings_env) -> None:
    _protect_all(settings_env)
    from services.api.routes import ingest as ingest_module

    monkeypatch.setattr(
        ingest_module.task_import_file,
        "apply_async",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("task should not run without ops role")
        ),
    )

    _set_override(api_app, get_principal, _viewer_principal())
    try:
        resp = await api_client.post("/ingest", json={"uri": "s3://sample.csv"})
        assert resp.status_code == 403
    finally:
        _clear_override(api_app, get_principal)


@pytest.mark.asyncio
async def test_ingest_accepts_ops_payload(api_app, api_client, monkeypatch, settings_env) -> None:
    _protect_all(settings_env)
    from services.api.routes import ingest as ingest_module

    calls: list[tuple[tuple, dict]] = []

    class _Result(SimpleNamespace):
        id: str

    def _fake_apply_async(*args, **kwargs):
        calls.append((args, kwargs))
        return _Result(id="task-123")

    monkeypatch.setattr(ingest_module.task_import_file, "apply_async", _fake_apply_async)
    _set_override(api_app, get_principal, _ops_principal())
    try:
        resp = await api_client.post("/ingest", json={"uri": "s3://rates.csv", "force": True})
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["task_id"] == "task-123"
        assert calls, "apply_async should be invoked for ops user"
    finally:
        _clear_override(api_app, get_principal)


def _ensure_admin_route(api_app) -> None:
    if getattr(api_app.state, "admin_probe_registered", False):
        return

    async def _admin_probe() -> Response:
        return Response(status_code=204)

    api_app.add_api_route(
        "/__admin-probe",
        _admin_probe,
        methods=["GET"],
        dependencies=[Depends(require_admin)],
    )
    api_app.state.admin_probe_registered = True


@pytest.mark.asyncio
async def test_admin_route_requires_admin_role(api_app, api_client, settings_env) -> None:
    _protect_all(settings_env)
    _ensure_admin_route(api_app)
    _set_override(api_app, get_principal, _ops_principal())
    try:
        resp = await api_client.get("/__admin-probe")
        assert resp.status_code == 403
    finally:
        _clear_override(api_app, get_principal)


@pytest.mark.asyncio
async def test_admin_route_allows_admin(api_app, api_client, settings_env) -> None:
    _protect_all(settings_env)
    _ensure_admin_route(api_app)
    _set_override(api_app, get_principal, _admin_principal())
    try:
        resp = await api_client.get("/__admin-probe")
        assert resp.status_code == 204
    finally:
        _clear_override(api_app, get_principal)


@pytest.mark.asyncio
async def test_roi_route_returns_rows(
    api_app, api_client, fake_db_session, monkeypatch, settings_env
) -> None:
    _protect_all(settings_env)
    session = fake_db_session(_StubResult())

    async def _session_override() -> AsyncIterator[object]:
        yield session

    async def _fake_fetch(session, roi_min, vendor, category):
        return [{"asin": "A1", "roi_pct": 12.5, "vendor": vendor, "category": category}]

    monkeypatch.setattr(roi_module.roi_repository, "fetch_roi_rows", _fake_fetch)
    _set_override(api_app, get_session, _session_override)
    _set_override(api_app, get_principal, _viewer_principal())
    _set_override(api_app, roi_module.require_basic_auth, lambda: None)
    try:
        resp = await api_client.get(
            "/roi", params={"roi_min": 10, "vendor": 101, "category": "Toys"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["asin"] == "A1"
        assert data[0]["vendor"] == 101
    finally:
        _clear_override(api_app, get_session)
        _clear_override(api_app, get_principal)
        _clear_override(api_app, roi_module.require_basic_auth)


@pytest.mark.asyncio
async def test_roi_invalid_query_returns_422(api_app, api_client, settings_env) -> None:
    _protect_all(settings_env)
    _set_override(api_app, get_principal, _viewer_principal())
    _set_override(api_app, roi_module.require_basic_auth, lambda: None)
    resp = await api_client.get("/roi", params={"roi_min": "not-a-number"})
    try:
        assert resp.status_code == 422
    finally:
        _clear_override(api_app, get_principal)
        _clear_override(api_app, roi_module.require_basic_auth)


@pytest.mark.asyncio
async def test_score_invalid_body_returns_422(api_app, api_client, settings_env) -> None:
    _protect_all(settings_env)
    _set_override(api_app, get_principal, _viewer_principal())
    _set_override(api_app, score_module.require_basic_auth, lambda: None)
    try:
        resp = await api_client.post("/score", json={"asins": []})
        assert resp.status_code == 422
    finally:
        _clear_override(api_app, get_principal)
        _clear_override(api_app, score_module.require_basic_auth)


def test_stats_kpi_sql_path(monkeypatch) -> None:
    monkeypatch.setenv("STATS_USE_SQL", "1")

    class _Result:
        def __init__(self, data):
            self._data = data

        def mappings(self):
            return self

        def first(self):
            return self._data

    class _FakeDB:
        def execute(self, _stmt):
            return _Result({"roi_avg": 1.5, "products": 3, "vendors": 2})

    result = stats_module.kpi(db=_FakeDB())
    assert result["kpi"]["roi_avg"] == pytest.approx(1.5)
    assert result["kpi"]["products"] == 3
    assert result["kpi"]["vendors"] == 2


def test_stats_kpi_defaults_without_db(monkeypatch) -> None:
    monkeypatch.setenv("STATS_USE_SQL", "1")
    result = stats_module.kpi(db=None)
    assert result["kpi"] == {"roi_avg": 0.0, "products": 0, "vendors": 0}
