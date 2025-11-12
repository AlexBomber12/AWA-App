from __future__ import annotations

import types

import pytest
from starlette.requests import Request

from services.api.routes import roi as roi_module


def _request() -> Request:
    scope = {"type": "http", "method": "GET", "path": "/roi-review", "headers": []}
    return Request(scope, receive=lambda: None)


@pytest.mark.asyncio
async def test_roi_review_context_only_has_rows(monkeypatch):
    async def _fake_fetch(session, roi_min, vendor, category):
        return [{"asin": "B1"}]

    monkeypatch.setattr(roi_module.roi_repository, "fetch_pending_rows", _fake_fetch)
    captured = {}

    def _capture(template_name, context):
        captured["context"] = context
        return types.SimpleNamespace(template=template_name, context=context)

    monkeypatch.setattr(roi_module.templates, "TemplateResponse", _capture)

    response = await roi_module.roi_review(_request(), roi_min=0, vendor=None, session=object())
    assert response.context["rows"][0]["asin"] == "B1"
    assert "items" not in response.context


def test_roi_template_renders_without_items() -> None:
    template = roi_module.templates.get_template("roi_review.html")
    html = template.render(
        {
            "rows": [
                {
                    "asin": "B1",
                    "title": "Widget",
                    "vendor_id": "V1",
                    "cost": 10,
                    "freight": 1,
                    "fees": 2,
                    "roi_pct": 25,
                }
            ],
        }
    )
    assert "B1" in html
