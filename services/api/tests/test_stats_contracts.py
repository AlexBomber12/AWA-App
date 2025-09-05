import os
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@contextmanager
def client_with_auth():
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    from services.api.main import app

    with TestClient(app) as client:
        yield client, ("u", "p")


def _auth_headers(u, p):
    import base64

    token = base64.b64encode(f"{u}:{p}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_kpi_contract():
    with client_with_auth() as (client, up):
        r = client.get("/stats/kpi", headers=_auth_headers(*up))
        assert r.status_code == 200
        data = r.json()
        assert "kpi" in data and {"roi_avg", "products", "vendors"} <= set(
            data["kpi"].keys()
        )
        assert isinstance(data["kpi"]["roi_avg"], (int, float))


def test_roi_by_vendor_contract():
    with client_with_auth() as (client, up):
        r = client.get("/stats/roi_by_vendor", headers=_auth_headers(*up))
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and "total_vendors" in data
        assert isinstance(data["items"], list)


def test_roi_trend_contract():
    with client_with_auth() as (client, up):
        r = client.get("/stats/roi_trend", headers=_auth_headers(*up))
        assert r.status_code == 200
        data = r.json()
        assert "points" in data
        assert isinstance(data["points"], list)
