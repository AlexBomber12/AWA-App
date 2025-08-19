import base64
import os

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def _auth_headers(u, p):
    token = base64.b64encode(f"{u}:{p}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _client():
    from services.api.main import app

    return TestClient(app)


def test_roi_needs_basic_auth(monkeypatch):
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    with _client() as client:
        r = client.get("/roi")  # no auth
        assert r.status_code in (401, 403)


def test_roi_basic_auth_good(monkeypatch):
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    with _client() as client:
        r = client.get("/roi", headers=_auth_headers("u", "p"))
        assert r.status_code == 200


def test_score_needs_basic_auth():
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    with _client() as client:
        r = client.post("/score", json={"asins": ["A1"]})  # no auth
        assert r.status_code in (401, 403)


def test_stats_contract_needs_basic_auth():
    os.environ["API_BASIC_USER"] = "u"
    os.environ["API_BASIC_PASS"] = "p"
    with _client() as client:
        r = client.get("/stats/kpi")
        assert r.status_code in (401, 403)
