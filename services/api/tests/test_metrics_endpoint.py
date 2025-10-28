from fastapi.testclient import TestClient

from services.api.main import app


def test_metrics_endpoint_returns_prometheus_text() -> None:
    with TestClient(app) as client:
        client.get("/ready")
        response = client.get("/metrics")

    assert response.status_code == 200
    body = response.text
    assert "requests_total" in body
    assert "request_duration_seconds_bucket" in body
