from __future__ import annotations

from io import BytesIO

from fastapi import UploadFile
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
