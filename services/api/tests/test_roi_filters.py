import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

pytestmark = pytest.mark.integration


def _auth_headers():
    import base64

    token = base64.b64encode(b"u:p").decode()
    return {"Authorization": f"Basic {token}"}


def setup_test_view(pg_engine):
    with pg_engine.begin() as c:
        c.execute(
            text("""
            CREATE TABLE IF NOT EXISTS test_roi_view(
                asin text primary key,
                vendor text,
                category text,
                roi numeric
            );
        """)
        )
        c.execute(text("TRUNCATE test_roi_view;"))
        c.execute(
            text("""
            INSERT INTO test_roi_view(asin,vendor,category,roi) VALUES
            ('A1','V1','Beauty', 45.0),
            ('A2','V1','Electronics', 10.0),
            ('A3','V2','Beauty', 75.0),
            ('A4','V3','Sports', 30.0)
        """)
        )


def client():
    from services.api.main import app

    return TestClient(app)


def test_roi_filtering_by_min_vendor_category(pg_engine, monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    os.environ["ROI_VIEW_NAME"] = "test_roi_view"
    setup_test_view(pg_engine)

    c = client()
    # roi_min
    r = c.get("/roi?roi_min=40", headers=_auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert all(item.get("roi", 0) >= 40 for item in data)

    # vendor
    r = c.get("/roi?vendor=V1", headers=_auth_headers())
    assert r.status_code == 200
    vendors = {x.get("vendor") for x in r.json()}
    assert vendors == {"V1"}

    # category + roi_min
    r = c.get("/roi?category=Beauty&roi_min=50", headers=_auth_headers())
    assert r.status_code == 200
    rows = r.json()
    assert all(x.get("category") == "Beauty" and x.get("roi", 0) >= 50 for x in rows)
