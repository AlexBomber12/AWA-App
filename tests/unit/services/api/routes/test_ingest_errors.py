import json
from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.requests import Request

from services.api.ingest_utils import ApiError, IngestUpload
from services.api.routes import ingest as ingest_module


def _request(payload: dict[str, object] | None = None) -> Request:
    async def _json() -> dict[str, object]:
        return payload or {}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/ingest",
        "headers": [],
    }
    req = Request(scope, receive=lambda: None)
    req.json = _json  # type: ignore[assignment]
    return req


def _response_payload(response) -> dict[str, object]:
    return json.loads(response.body.decode())


@pytest.mark.asyncio
async def test_submit_ingest_rejects_unsupported_extension():
    upload = UploadFile(filename="report.pdf", file=BytesIO(b"pdf-content"))
    response = await ingest_module.submit_ingest(_request({}), file=upload)
    assert response.status_code == 400
    payload = _response_payload(response)
    assert payload["error"]["code"] == "unsupported_file_format"
    assert "report.pdf" not in payload["error"]["detail"]
    assert payload["error"]["hint"]


@pytest.mark.asyncio
async def test_submit_ingest_missing_payload_returns_400():
    response = await ingest_module.submit_ingest(_request({}), file=None)
    assert response.status_code == 400
    payload = _response_payload(response)
    assert payload["error"]["code"] == "bad_request"
    assert "file upload" in payload["error"]["detail"]


@pytest.mark.asyncio
async def test_submit_ingest_returns_422_for_schema_errors(monkeypatch):
    async def fake_download(_uri: str, log=None):
        return IngestUpload(
            uri="file:///tmp/schema.csv",
            digest="digest",
            total_bytes=2,
            extension="csv",
        )

    def fake_enqueue(*_args, **_kwargs):
        raise ApiError(status_code=422, code="unprocessable_entity", detail="unknown columns")

    monkeypatch.setattr(ingest_module, "download_uri_to_temp", fake_download)
    monkeypatch.setattr(ingest_module, "enqueue_import_task", fake_enqueue)

    response = await ingest_module.submit_ingest(_request({"uri": "s3://bucket/object.csv"}), file=None)
    assert response.status_code == 422
    payload = _response_payload(response)
    assert payload["error"]["code"] == "unprocessable_entity"
    assert "unknown columns" in payload["error"]["detail"]
