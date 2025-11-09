import pytest
from fastapi import HTTPException

from services.api.routes import score as score_module


class DummySession:
    """Captures calls made by the score route for assertions."""

    def __init__(self):
        self.calls = 0


@pytest.mark.asyncio
async def test_score_validates_non_empty_body():
    with pytest.raises(HTTPException) as excinfo:
        await score_module.score(score_module.ScoreRequest(asins=[]), session=DummySession())
    assert excinfo.value.status_code == 422


@pytest.mark.asyncio
async def test_score_preserves_input_order_and_not_found_holes(monkeypatch):
    async def _fake_fetch(session, asins, roi_view):
        return {
            "A1": {"vendor": "V1", "category": "C1", "roi": 1.2},
            "C3": {"vendor": "V3", "category": None, "roi": None},
        }

    monkeypatch.setattr(score_module.roi_repository, "fetch_scores_for_asins", _fake_fetch)
    monkeypatch.setattr(score_module, "get_roi_view_name", lambda: "v_roi_full")

    body = score_module.ScoreRequest(asins=["A1", "B2", "C3", "B2"])
    resp = await score_module.score(body, session=DummySession())

    assert [item.asin for item in resp.items] == ["A1", "B2", "C3", "B2"]
    assert resp.items[0].vendor == "V1"
    assert resp.items[1].error == "not_found"
    assert resp.items[2].vendor == "V3"
    assert resp.items[3].error == "not_found"


@pytest.mark.asyncio
async def test_score_single_query_path_mock_db_repo(monkeypatch):
    calls: list[tuple[tuple[str, ...], str]] = []

    async def _fake_fetch(session, asins, roi_view):
        calls.append((tuple(asins), roi_view))
        return {}

    monkeypatch.setattr(score_module.roi_repository, "fetch_scores_for_asins", _fake_fetch)
    monkeypatch.setattr(score_module, "get_roi_view_name", lambda: "mat_v_roi_full")

    body = score_module.ScoreRequest(asins=["A1", "A1", "B2"])
    await score_module.score(body, session=DummySession())

    assert len(calls) == 1
    queried_asins, view = calls[0]
    assert view == "mat_v_roi_full"
    assert queried_asins == ("A1", "A1", "B2")


@pytest.mark.asyncio
async def test_score_invalid_view_returns_http_400(monkeypatch):
    monkeypatch.setattr(
        score_module,
        "get_roi_view_name",
        lambda: (_ for _ in ()).throw(score_module.InvalidROIViewError("nope")),
    )
    body = score_module.ScoreRequest(asins=["A1"])
    with pytest.raises(HTTPException) as excinfo:
        await score_module.score(body, session=DummySession())
    assert excinfo.value.status_code == 400
