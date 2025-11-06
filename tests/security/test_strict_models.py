from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api.routes.score import ScoreRequest


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.post("/score")
    def score(body: ScoreRequest) -> ScoreRequest:
        return body

    return app


def test_extra_field_rejected():
    app = _build_app()
    with TestClient(app) as client:
        response = client.post("/score", json={"asins": ["B001"], "extra": "value"})
        assert response.status_code == 422


def test_whitespace_trimmed():
    app = _build_app()
    with TestClient(app) as client:
        response = client.post("/score", json={"asins": ["  B002  "]})
        assert response.status_code == 200
        assert response.json()["asins"] == ["B002"]


def test_wrong_type_rejected():
    app = _build_app()
    with TestClient(app) as client:
        response = client.post("/score", json={"asins": [12345]})
        assert response.status_code == 422
