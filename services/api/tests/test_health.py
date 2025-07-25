from fastapi.testclient import TestClient

from services.api.main import app


def test_health_route() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
