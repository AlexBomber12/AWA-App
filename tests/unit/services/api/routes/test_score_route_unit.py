import types

import pytest
from fastapi import HTTPException

from services.api.routes import score as score_module


class DummyRow:
    def __init__(self, asin, vendor=None, category=None, roi=None):
        self.asin = asin
        self.vendor = vendor
        self.category = category
        self.roi = roi


class DummyDB:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def execute(self, stmt, params):
        self.calls.append((str(stmt), params))
        asin = params["asin"]
        return types.SimpleNamespace(fetchone=lambda: self.rows.get(asin))


def test_score_validates_non_empty_body():
    with pytest.raises(HTTPException) as excinfo:
        score_module.score(score_module.ScoreRequest(asins=[]), db=None)
    assert excinfo.value.status_code == 422


def test_score_returns_found_rows():
    db = DummyDB({"A1": DummyRow("A1", vendor="V", category="C", roi=1.5)})
    body = score_module.ScoreRequest(asins=["A1", "B2"])
    resp = score_module.score(body, db=db)
    items = {item.asin: item for item in resp.items}
    assert items["A1"].vendor == "V"
    assert items["B2"].error == "not_found"
    assert db.calls[0][1]["asin"] == "A1"
