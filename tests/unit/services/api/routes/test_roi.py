import types

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from services.api.routes import roi as roi_module
from services.api.schemas import RoiApprovalResponse, RoiListResponse, RoiRow
from tests.unit.conftest import _StubResult


@pytest.mark.asyncio
async def test_roi_returns_typed_rows(fake_db_session):
    session = fake_db_session(_StubResult(mappings=[{"asin": "A1", "roi_pct": 12.3, "total_count": 1}]))
    result = await roi_module.roi(session=session, roi_min=10)
    assert isinstance(result, RoiListResponse)
    assert len(result.items) == 1
    assert isinstance(result.items[0], RoiRow)
    assert result.items[0].roi_pct == 12.3
    assert result.pagination.total == 1


@pytest.mark.asyncio
async def test_roi_invalid_view_returns_http_400(monkeypatch):
    async def _raise(*_args, **_kwargs):
        raise roi_module.InvalidROIViewError("bad view")

    monkeypatch.setattr(roi_module.roi_repository, "fetch_roi_rows", _raise)
    with pytest.raises(HTTPException) as excinfo:
        await roi_module.roi(session=None)
    assert excinfo.value.status_code == 400


def _make_request() -> Request:
    scope = {"type": "http", "method": "GET", "path": "/roi-review", "headers": []}
    return Request(scope, receive=lambda: None)


@pytest.mark.asyncio
async def test_roi_review_renders(monkeypatch):
    captured = {}

    class DummyResponse:
        def __init__(self, template, context):
            self.template = template
            self.context = context

    async def _fake_fetch(session, roi_min, vendor, category):
        captured["args"] = (roi_min, vendor, category)
        return [{"asin": "A1"}]

    monkeypatch.setattr(roi_module.roi_repository, "fetch_pending_rows", _fake_fetch)
    monkeypatch.setattr(
        roi_module.templates,
        "TemplateResponse",
        lambda template, context: DummyResponse(template, context),
    )

    response = await roi_module.roi_review(_make_request(), roi_min=5, vendor=7, session=object())
    assert response.template == "roi_review.html"
    assert response.context["rows"][0]["asin"] == "A1"
    assert captured["args"] == (5, 7, None)


@pytest.mark.asyncio
async def test_approve_updates_when_asins(monkeypatch):
    recorded = {}

    async def _fake_bulk(session, asins, approved_by=None):
        recorded["asins"] = asins
        recorded["approved_by"] = approved_by
        return ["A1", "A2"]

    class DummyRequest:
        headers = {"content-type": "application/json"}
        state = types.SimpleNamespace(user=types.SimpleNamespace(email="ops@example.com"))

        async def json(self):
            return {"asins": ["A1", "A2"]}

        async def form(self):
            return types.SimpleNamespace(getlist=lambda key: [])

    monkeypatch.setattr(roi_module.roi_repository, "bulk_approve", _fake_bulk)

    result = await roi_module.approve(DummyRequest(), session=object())
    assert isinstance(result, RoiApprovalResponse)
    assert result.updated == 2
    assert result.approved_ids == ["A1", "A2"]
    assert recorded["asins"] == ["A1", "A2"]
    assert recorded["approved_by"] == "ops@example.com"


@pytest.mark.asyncio
async def test_approve_raises_when_no_asins():
    class DummyRequest:
        headers = {"content-type": "application/json"}
        state = types.SimpleNamespace(user=None)

        async def json(self):
            return {}

        async def form(self):
            return types.SimpleNamespace(getlist=lambda key: [])

    with pytest.raises(HTTPException) as excinfo:
        await roi_module.approve(DummyRequest(), session=object(), _=object(), __=object())
    assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test_approve_returns_404_when_no_rows(monkeypatch):
    async def _fake_bulk(session, asins, approved_by=None):
        return []

    class DummyRequest:
        headers = {"content-type": "application/json"}
        state = types.SimpleNamespace(user=None)

        async def json(self):
            return {"asins": ["A1"]}

        async def form(self):
            return types.SimpleNamespace(getlist=lambda key: [])

    monkeypatch.setattr(roi_module.roi_repository, "bulk_approve", _fake_bulk)
    with pytest.raises(HTTPException) as excinfo:
        await roi_module.approve(DummyRequest(), session=object())
    assert excinfo.value.status_code == 404
