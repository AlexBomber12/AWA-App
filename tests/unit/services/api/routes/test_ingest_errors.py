import json
from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.requests import Request

from etl.load_csv import ImportValidationError
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
    assert payload["code"] == "unsupported_file_format"
    assert "report.pdf" not in payload["detail"]
    assert payload["hint"]


@pytest.mark.asyncio
async def test_submit_ingest_missing_payload_returns_400():
    response = await ingest_module.submit_ingest(_request({}), file=None)
    assert response.status_code == 400
    payload = _response_payload(response)
    assert payload["code"] == "bad_request"
    assert "file upload" in payload["detail"]


@pytest.mark.asyncio
async def test_submit_ingest_returns_422_for_schema_errors(monkeypatch, tmp_path):
    class DummyAsync:
        def __init__(self):
            self.id = "boom"
            self.info = ImportValidationError("unknown columns")

        def get(self, propagate=False):
            raise ImportValidationError("unknown columns")

        def failed(self):
            return True

    remote = tmp_path / "schema.csv"
    remote.write_text("a,b", encoding="utf-8")

    async def fake_download(_uri: str):
        return remote, "digest"

    monkeypatch.setattr(ingest_module, "_download_remote", fake_download)
    monkeypatch.setattr(ingest_module.task_import_file, "apply_async", lambda *a, **k: DummyAsync())
    monkeypatch.setattr(ingest_module.celery_app.conf, "task_always_eager", True, raising=False)

    response = await ingest_module.submit_ingest(_request({"uri": "s3://bucket/object.csv"}), file=None)
    assert response.status_code == 422
    payload = _response_payload(response)
    assert payload["code"] == "unprocessable_entity"
    assert "unknown columns" in payload["detail"]
