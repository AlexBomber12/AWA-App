from fastapi.testclient import TestClient

from services.api import db
from services.api.main import app


class FakeSession:
    async def execute(self, query):
        class R:
            def scalar(self):
                import datetime

                return datetime.datetime.utcnow()

        return R()


async def fake_get_session():
    yield FakeSession()


def test_health_endpoint(monkeypatch):
    app.dependency_overrides[db.get_session] = fake_get_session
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    app.dependency_overrides.clear()
