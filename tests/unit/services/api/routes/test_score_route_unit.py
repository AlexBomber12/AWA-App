import types

import pytest
from fastapi import HTTPException

from services.api.routes import score as score_module


class DummyResult:
    def __init__(self, rows):
        self._rows = rows

    def __iter__(self):
        for row in self._rows:
            yield types.SimpleNamespace(**row)


class DummySession:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    async def execute(self, stmt, params):
        self.calls.append((str(stmt), params))
        asins = set(params["asins"])
        matching = [row for row in self.rows if row["asin"] in asins]
        return DummyResult(matching)


@pytest.mark.asyncio
async def test_score_validates_non_empty_body():
    with pytest.raises(HTTPException) as excinfo:
        await score_module.score(score_module.ScoreRequest(asins=[]), session=DummySession([]))
    assert excinfo.value.status_code == 422


@pytest.mark.asyncio
async def test_score_returns_found_rows(monkeypatch):
    session = DummySession([{"asin": "A1", "vendor": "V", "category": "C", "roi": 1.5}])
    body = score_module.ScoreRequest(asins=["A1", "B2"])
    resp = await score_module.score(body, session=session)
    items = {item.asin: item for item in resp.items}
    assert items["A1"].vendor == "V"
    assert items["B2"].error == "not_found"
    assert "WHERE asin IN" in session.calls[0][0]


@pytest.mark.asyncio
async def test_score_invalid_view_returns_http_400(monkeypatch):
    monkeypatch.setattr(
        score_module,
        "current_roi_view",
        lambda: (_ for _ in ()).throw(score_module.InvalidROIViewError("nope")),
    )
    body = score_module.ScoreRequest(asins=["A1"])
    with pytest.raises(HTTPException) as excinfo:
        await score_module.score(body, session=DummySession([]))
    assert excinfo.value.status_code == 400
