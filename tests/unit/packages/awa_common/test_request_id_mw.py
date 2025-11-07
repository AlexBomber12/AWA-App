import uuid

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from awa_common.logging import RequestIdMiddleware


def _build_app():
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)

    @app.get("/ping")
    def ping(request: Request):
        return {"request_id": request.state.request_id, "trace_id": request.state.trace_id}

    return app


def test_request_id_middleware_generates_header() -> None:
    app = _build_app()
    with TestClient(app) as client:
        response = client.get("/ping")

    assert response.status_code == 200
    outgoing_id = response.headers.get("X-Request-ID")
    assert outgoing_id
    uuid_obj = uuid.UUID(outgoing_id)
    assert response.json()["request_id"] == str(uuid_obj)
    assert response.headers.get("X-Trace-ID") == response.json()["trace_id"]


def test_request_id_middleware_respects_existing_header() -> None:
    app = _build_app()
    custom_id = "req-12345"
    with TestClient(app) as client:
        response = client.get("/ping", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id
    assert response.json()["request_id"] == custom_id
