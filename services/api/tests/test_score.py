import os
from fastapi.testclient import TestClient
from sqlalchemy import text
import pytest
pytestmark = pytest.mark.integration


def _auth_headers():
    import base64
    token = base64.b64encode(b"u:p").decode()
    return {"Authorization": f"Basic {token}"}


def setup_test_view(pg_engine):
    with pg_engine.begin() as c:
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS test_roi_view(
                asin text primary key,
                vendor text,
                category text,
                roi numeric
            );
        """))
        c.execute(text("TRUNCATE test_roi_view;"))
        c.execute(text("""
            INSERT INTO test_roi_view(asin,vendor,category,roi) VALUES
            ('A1','V1','Beauty', 55.5),
            ('A3','V2','Beauty', 12.0)
        """))


def client():
    from services.api.main import app
    return TestClient(app)


def test_score_mixed_found_not_found(pg_engine):
    os.environ["TESTING"] = "1"
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    os.environ["ROI_VIEW_NAME"] = "test_roi_view"
    setup_test_view(pg_engine)

    c = client()
    r = c.post("/score", json={"asins": ["A1", "BAD", "A3"]}, headers=_auth_headers())
    assert r.status_code == 200
    data = r.json()["items"]
    by_asin = {d["asin"]: d for d in data}
    assert by_asin["A1"]["roi"] == 55.5
    assert by_asin["A3"]["roi"] == 12.0
    assert by_asin["BAD"]["error"] == "not_found"


def test_score_validation_requires_non_empty_list():
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    c = client()
    r = c.post("/score", json={"asins": []}, headers=_auth_headers())
    assert r.status_code in (400, 422)
