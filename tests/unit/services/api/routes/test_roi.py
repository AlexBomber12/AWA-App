import types

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials
from starlette.requests import Request

from services.api.routes import roi as roi_module
from tests.unit.conftest import _StubResult


@pytest.mark.asyncio
async def test_roi_returns_dict_rows(fake_db_session):
    session = fake_db_session(_StubResult(mappings=[{"asin": "A1", "roi_pct": 12.3}]))
    result = await roi_module.roi(session=session, roi_min=10)
    assert result == [{"asin": "A1", "roi_pct": 12.3}]


def test_check_basic_auth_success(monkeypatch):
    monkeypatch.setenv("BASIC_USER", "user")
    monkeypatch.setenv("BASIC_PASS", "pass")
    creds = HTTPBasicCredentials(username="user", password="pass")
    assert roi_module._check_basic_auth(creds) == "user"


def test_check_basic_auth_failure(monkeypatch):
    monkeypatch.setenv("BASIC_USER", "user")
    monkeypatch.setenv("BASIC_PASS", "pass")
    creds = HTTPBasicCredentials(username="bad", password="pass")
    with pytest.raises(HTTPException):
        roi_module._check_basic_auth(creds)


def test_build_pending_sql_adds_filters():
    stmt = roi_module.build_pending_sql(True, True)
    compiled = str(stmt)
    assert "vendor_id" in compiled
    assert "category" in compiled


def _make_request() -> Request:
    scope = {"type": "http", "method": "GET", "path": "/roi-review", "headers": []}
    return Request(scope, receive=lambda: None)


def test_roi_review_renders(monkeypatch):
    captured = {}

    class DummyResponse:
        def __init__(self, template, context):
            self.template = template
            self.context = context

    class DummyConn:
        def execute(self, stmt, params):
            captured["params"] = params

            class DummyResult:
                def fetchall(self):
                    return [types.SimpleNamespace(_mapping={"asin": "A1"})]

            return DummyResult()

    class DummyEngine:
        def connect(self):
            return self

        def __enter__(self):
            return DummyConn()

        def __exit__(self, exc_type, exc, tb):
            return False

        def dispose(self):
            captured["disposed"] = True

    monkeypatch.setattr(roi_module, "build_dsn", lambda **_: "postgresql://test")
    monkeypatch.setattr(roi_module, "create_engine", lambda *_: DummyEngine())
    monkeypatch.setattr(
        roi_module.templates,
        "TemplateResponse",
        lambda template, context: DummyResponse(template, context),
    )

    response = roi_module.roi_review(_make_request(), roi_min=5, vendor=7)
    assert response.template == "roi_review.html"
    assert response.context["rows"][0]["asin"] == "A1"
    assert captured["params"]["roi_min"] == 5


@pytest.mark.asyncio
async def test_approve_updates_when_asins(monkeypatch):
    recorded = {}

    class DummyConn:
        def __init__(self):
            self.calls = []

        def execute(self, stmt, params):
            recorded["params"] = params

            class DummyScalars:
                def all(self_inner):
                    return ["A1", "A2"]

            return types.SimpleNamespace(scalars=lambda: DummyScalars())

    class DummyEngine:
        def __init__(self):
            self.conn = DummyConn()

        def begin(self):
            return self

        def __enter__(self):
            return self.conn

        def __exit__(self, exc_type, exc, tb):
            return False

        def dispose(self):
            recorded["disposed"] = True

    class DummyRequest:
        headers = {"content-type": "application/json"}

        async def json(self):
            return {"asins": ["A1", "A2"]}

        async def form(self):
            return types.SimpleNamespace(getlist=lambda key: [])

    monkeypatch.setattr(roi_module, "build_dsn", lambda **_: "postgresql://test")
    monkeypatch.setattr(roi_module, "create_engine", lambda *_: DummyEngine())

    result = await roi_module.approve(DummyRequest())
    assert result == {"updated": 2}
    assert recorded["params"]["asins"] == ["A1", "A2"]


@pytest.mark.asyncio
async def test_approve_no_asins_returns_zero(monkeypatch):
    class DummyRequest:
        headers = {"content-type": "application/json"}

        async def json(self):
            return {}

        async def form(self):
            return types.SimpleNamespace(getlist=lambda key: [])

    result = await roi_module.approve(DummyRequest())
    assert result == {"updated": 0}
