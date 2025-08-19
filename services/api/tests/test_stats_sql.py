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
                asin text,
                vendor text,
                category text,
                roi numeric,
                dt date
            );
        """))
        c.execute(text("TRUNCATE test_roi_view;"))
        c.execute(text("""
            INSERT INTO test_roi_view(asin,vendor,category,roi,dt) VALUES
            ('A1','V1','Beauty', 50.0, '2024-01-15'),
            ('A2','V1','Beauty', 10.0, '2024-02-10'),
            ('A3','V2','Sports', 70.0, '2024-02-20'),
            ('A4','V2','Sports', 30.0, '2024-03-05');
        """))


def client():
    from services.api.main import app
    return TestClient(app)


def test_stats_sql_mode_kpi_vendor_trend(pg_engine, monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["STATS_USE_SQL"] = "1"
    os.environ["ROI_VIEW_NAME"] = "test_roi_view"
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    setup_test_view(pg_engine)

    c = client()

    r = c.get("/stats/kpi", headers=_auth_headers())
    assert r.status_code == 200
    kpi = r.json()["kpi"]
    assert kpi["products"] == 4 and kpi["vendors"] == 2
    assert 39.9 < kpi["roi_avg"] < 40.1

    r = c.get("/stats/roi_by_vendor", headers=_auth_headers())
    data = r.json()
    vendors = {item["vendor"]: item for item in data["items"]}
    assert vendors["V1"]["items"] == 2 and 29.9 < vendors["V1"]["roi_avg"] < 30.1
    assert vendors["V2"]["items"] == 2 and 49.9 < vendors["V2"]["roi_avg"] < 50.1

    r = c.get("/stats/roi_trend", headers=_auth_headers())
    points = r.json()["points"]
    months = {p["month"]: p for p in points}
    assert any(m.endswith("-01") for m in months)
