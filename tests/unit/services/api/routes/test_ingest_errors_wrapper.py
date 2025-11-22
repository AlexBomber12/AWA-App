from __future__ import annotations

import json

from starlette.requests import Request

from services.api.routes import ingest_errors


def test_ingest_errors_wrapper_responds():
    request = Request({"type": "http", "path": "/ingest", "headers": []})
    err = ingest_errors.IngestRequestError(status_code=400, code="bad_request", detail="oops")
    response = ingest_errors.respond_with_ingest_error(request, err, route="/ingest")
    assert response.status_code == 400
    payload = json.loads(response.body.decode())
    assert payload["error"]["code"] == "bad_request"
    assert payload["request_id"]
