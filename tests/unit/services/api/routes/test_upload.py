from __future__ import annotations

import json
from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.requests import Request

from services.api.ingest_utils import ApiError, IngestUpload
from services.api.routes import upload as upload_module


class DummyAsyncResult:
    def __init__(self) -> None:
        self.id = "task-123"

    def get(self, propagate: bool = False):  # pragma: no cover - eager mode
        return None


async def test_upload_streams_and_dispatches_task(monkeypatch):
    async def fake_upload_to_minio(*_a, **_k):
        return IngestUpload(
            uri="minio://bucket/key",
            digest="abc123",
            total_bytes=10,
            extension="csv",
            object_key="key",
        )

    recorded = {}

    def fake_enqueue(upload_target, *, report_type=None, force=False, log=None):
        recorded["upload"] = upload_target
        return DummyAsyncResult()

    monkeypatch.setattr(upload_module, "upload_file_to_minio", fake_upload_to_minio)
    monkeypatch.setattr(upload_module, "enqueue_import_task", fake_enqueue)
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    upload = UploadFile(filename="report.csv", file=BytesIO(b"col\n1\n"))
    response = await upload_module.upload(request, upload)
    assert response.status_code == 202
    payload = json.loads(response.body.decode())
    assert payload["idempotency_key"] == "abc123"
    assert recorded["upload"].digest == "abc123"


@pytest.mark.asyncio
async def test_upload_records_failure(monkeypatch):
    async def failing(*_a, **_k):
        raise ApiError(status_code=413, code="payload_too_large", detail="too big")

    monkeypatch.setattr(upload_module, "upload_file_to_minio", failing)
    request = Request({"type": "http", "headers": []})
    upload = UploadFile(filename="name.csv", file=BytesIO(b"data"))

    response = await upload_module.upload(request, upload)
    assert response.status_code == 413
    payload = json.loads(response.body.decode())
    assert payload["error"]["code"] == "payload_too_large"
    assert payload["error"]["detail"] == "too big"


@pytest.mark.asyncio
async def test_upload_handles_unexpected_exception(monkeypatch):
    async def boom(*_a, **_k):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(upload_module, "upload_file_to_minio", boom)
    request = Request({"type": "http", "headers": []})
    upload = UploadFile(filename="name.csv", file=BytesIO(b"data"))
    response = await upload_module.upload(request, upload)
    assert response.status_code == 500
    payload = json.loads(response.body.decode())
    assert payload["error"]["code"] == "bad_request"
