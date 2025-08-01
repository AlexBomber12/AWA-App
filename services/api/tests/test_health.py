from fastapi.testclient import TestClient

from services.api import db
from services.api.main import app


def test_health_route() -> None:
    class FakeSession:
        async def execute(self, query):
            class R:
                def scalar(self):
                    import datetime

                    return datetime.datetime.utcnow()

            return R()

    async def fake_get_session():
        yield FakeSession()

    app.dependency_overrides[db.get_session] = fake_get_session
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    app.dependency_overrides.clear()
