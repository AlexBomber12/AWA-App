from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST

from services.api.main import app


def test_metrics_endpoint_exposes_prometheus_metrics() -> None:
    with TestClient(app) as client:
        ready = client.get("/ready")
        assert ready.status_code == 200
        response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == CONTENT_TYPE_LATEST
    body = response.text
    assert "http_requests_total" in body
    assert 'method="GET"' in body
    assert 'status="200"' in body
    assert 'service="api"' in body
    assert "http_request_duration_seconds_bucket" in body
