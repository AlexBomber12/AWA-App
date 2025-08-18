import base64
import os

import psycopg
from fastapi.testclient import TestClient

from services.api import db as api_db
from services.api.main import app


def test_validation_error_json() -> None:
    prev_user = os.environ.get("BASIC_USER")
    prev_pass = os.environ.get("BASIC_PASS")
    os.environ["ROI_BASIC_AUTH_USER"] = "u"
    os.environ["ROI_BASIC_AUTH_PASSWORD"] = "p"
    os.environ["BASIC_USER"] = "u"
    os.environ["BASIC_PASS"] = "p"
    try:
        with TestClient(app) as client:
            auth = base64.b64encode(b"u:p").decode()
            resp = client.get(
                "/roi-review?vendor=abc", headers={"Authorization": f"Basic {auth}"}
            )
            assert resp.status_code == 422
            data = resp.json()
            assert data["error"]["type"] == "validation_error"
            assert data["error"]["message"] == "Invalid request"
            assert data["error"].get("request_id")
            assert isinstance(data.get("details"), list)
    finally:
        if prev_user is None:
            os.environ.pop("BASIC_USER", None)
        else:
            os.environ["BASIC_USER"] = prev_user
        if prev_pass is None:
            os.environ.pop("BASIC_PASS", None)
        else:
            os.environ["BASIC_PASS"] = prev_pass
        os.environ.pop("ROI_BASIC_AUTH_USER", None)
        os.environ.pop("ROI_BASIC_AUTH_PASSWORD", None)


def test_db_error_json() -> None:
    class BrokenSession:
        async def execute(self, *a, **kw):
            raise psycopg.OperationalError("connection lost")

    async def fake_get_session():
        yield BrokenSession()

    app.dependency_overrides[api_db.get_session] = fake_get_session
    try:
        with TestClient(app) as client:
            resp = client.get("/health")
            assert resp.status_code == 500
            assert resp.json()["error"]["type"] == "db_unavailable"
    finally:
        app.dependency_overrides.clear()
