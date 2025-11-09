from __future__ import annotations

import pytest

from services.api.app.repositories import roi as roi_repo
from services.api.routes import score as score_module, sku as sku_module, stats as stats_module
from tests.unit.conftest import _StubResult, _StubSession


def _patch_current_roi_view(
    monkeypatch: pytest.MonkeyPatch,
    target_module,
    *,
    attr: str = "current_roi_view",
    name: str = "test_roi_view",
):
    counter = {"count": 0}

    def _tracker():
        counter["count"] += 1
        return name

    monkeypatch.setattr(target_module, attr, _tracker)
    return counter


@pytest.mark.asyncio
async def test_score_route_invokes_singleton(monkeypatch):
    counter = _patch_current_roi_view(monkeypatch, score_module)
    session = _StubSession(_StubResult(mappings=[{"asin": "A1", "vendor": "V1", "category": "Cat", "roi": 12.3}]))
    body = score_module.ScoreRequest(asins=["A1"])
    await score_module.score(body, session=session)
    assert counter["count"] == 1


@pytest.mark.asyncio
async def test_sku_route_invokes_singleton(monkeypatch):
    counter = _patch_current_roi_view(monkeypatch, sku_module)
    card = _StubResult(mappings=[{"title": "Sample", "roi_pct": 10.0, "fees": 2.0}])
    chart = _StubResult(mappings=[])
    session = _StubSession(card, chart)
    await sku_module.get_sku("A1", session=session)
    assert counter["count"] == 1


@pytest.mark.asyncio
async def test_stats_route_invokes_singleton(monkeypatch):
    counter = _patch_current_roi_view(monkeypatch, stats_module)
    monkeypatch.setenv("STATS_USE_SQL", "1")
    session = _StubSession(_StubResult(mappings=[{"roi_avg": 10.0, "products": 1, "vendors": 1}]))
    await stats_module.kpi(session=session)
    assert counter["count"] == 1


@pytest.mark.asyncio
async def test_repository_uses_singleton(monkeypatch):
    counter = _patch_current_roi_view(monkeypatch, roi_repo)
    session = _StubSession(_StubResult(mappings=[]))
    await roi_repo.fetch_roi_rows(session, roi_min=0, vendor=None, category=None)
    assert counter["count"] == 1
