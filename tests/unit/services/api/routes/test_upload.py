from __future__ import annotations

from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from starlette.requests import Request

from services.api.routes import upload as upload_module


class DummyAsyncResult:
    def __init__(self) -> None:
        self.id = "task-123"

    def get(self, propagate: bool = False):  # pragma: no cover - eager mode
        return None


async def test_upload_streams_and_dispatches_task(monkeypatch):
    async def fake_stream(*_a, **_k):
        return 10, "abc123"

    monkeypatch.setattr(upload_module, "_upload_stream_to_s3", fake_stream)

    recorded = {}

    def fake_apply_async(*_a, **kwargs):
        recorded.update(kwargs)
        return DummyAsyncResult()

    monkeypatch.setattr(upload_module.task_import_file, "apply_async", fake_apply_async)
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    upload = UploadFile(filename="report.csv", file=BytesIO(b"col\n1\n"))
    response = await upload_module.upload(request, upload)
    assert response.status_code == 202
    assert recorded["kwargs"]["idempotency_key"] == "abc123"


def test_ensure_size_limit_enforces_header():
    request = Request({"type": "http", "headers": [(b"content-length", b"1024")]})
    upload_module._ensure_size_limit(request, max_bytes=2048)
    with pytest.raises(HTTPException):
        upload_module._ensure_size_limit(request, max_bytes=100)


def test_ensure_size_limit_ignores_bad_header():
    request = Request({"type": "http", "headers": [(b"content-length", b"invalid")]})
    upload_module._ensure_size_limit(request, max_bytes=1)


@pytest.mark.asyncio
async def test_upload_records_failure(monkeypatch):
    async def failing(*_a, **_k):
        raise HTTPException(status_code=413, detail="too big")

    fail_called = {}

    monkeypatch.setattr(upload_module, "_upload_stream_to_s3", failing)
    monkeypatch.setattr(
        upload_module, "record_ingest_upload_failure", lambda **_k: fail_called.setdefault("called", True)
    )
    request = Request({"type": "http", "headers": []})
    upload = UploadFile(filename="name.csv", file=BytesIO(b"data"))

    with pytest.raises(HTTPException):
        await upload_module.upload(request, upload)
    assert fail_called.get("called") is True
