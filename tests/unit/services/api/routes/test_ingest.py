import json
from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.requests import Request

from services.api.ingest_utils import ApiError, IngestUpload
from services.api.routes import ingest as ingest_module


class DummyAsyncResult:
    def __init__(self, state="SUCCESS", info=None):
        self.id = "task-1"
        self.state = state
        self.info = info or {}


def _make_request(payload):
    async def _json():
        return payload

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/ingest",
        "headers": [(b"content-type", b"application/json")],
    }
    req = Request(scope, receive=lambda: None)
    req.json = _json  # type: ignore[assignment]
    return req


def _json_body(response):
    return json.loads(response.body.decode())


@pytest.mark.asyncio
async def test_submit_ingest_from_payload(monkeypatch, tmp_path):
    recorded = {}

    class DummyAsync:
        def __init__(self):
            self.id = "abc"

    def fake_enqueue(upload, *, report_type=None, force=False, log=None):
        recorded["upload"] = upload
        recorded["report_type"] = report_type
        recorded["force"] = force
        return DummyAsync()

    remote_file = tmp_path / "remote.csv"
    remote_file.write_text("a,b", encoding="utf-8")

    async def fake_remote(uri: str, log=None):
        return IngestUpload(
            uri=f"file://{remote_file}",
            digest="hash-1",
            total_bytes=3,
            extension="csv",
            path=remote_file,
        )

    monkeypatch.setattr(ingest_module, "download_uri_to_temp", fake_remote)
    monkeypatch.setattr(ingest_module, "enqueue_import_task", fake_enqueue)
    request = _make_request({"uri": "s3://bucket/file.csv", "report_type": "roi"})
    response = await ingest_module.submit_ingest(request, file=None)
    data = _json_body(response)
    assert data["task_id"] == "abc"
    assert recorded["report_type"] == "roi"
    assert recorded["upload"].digest == "hash-1"


@pytest.mark.asyncio
async def test_submit_ingest_from_file(monkeypatch):
    recorded = {}

    class DummyAsync:
        id = "file-task"

    def fake_enqueue(upload, *, report_type=None, force=False, log=None):
        recorded["upload"] = upload
        recorded["report_type"] = report_type
        recorded["force"] = force
        return DummyAsync()

    async def fake_persist(file, request, log=None):
        return IngestUpload(
            uri="file:///tmp/payload.csv",
            digest="abc123",
            total_bytes=10,
            extension="csv",
        )

    monkeypatch.setattr(ingest_module, "persist_upload_to_temp", fake_persist)
    monkeypatch.setattr(ingest_module, "enqueue_import_task", fake_enqueue)

    upload = UploadFile(filename="data.csv", file=BytesIO(b"a,b\n1,2\n"))
    request = _make_request({})
    response = await ingest_module.submit_ingest(request, file=upload)
    data = _json_body(response)
    assert data["task_id"] == "file-task"
    assert recorded["upload"].uri.startswith("file://")
    assert recorded["upload"].digest == "abc123"


@pytest.mark.asyncio
async def test_get_job_returns_meta_async(monkeypatch):
    def fake_async_result(task_id):
        return DummyAsyncResult(state="FAILURE", info={})

    monkeypatch.setattr(ingest_module.celery_app, "AsyncResult", fake_async_result)
    result = await ingest_module.get_job("abc")
    assert result["state"] == "FAILURE"
    assert result["meta"]["status"] == "error"


@pytest.mark.asyncio
async def test_submit_ingest_eager_failure_propagates(monkeypatch):
    async def fake_download(_uri: str, log=None):
        return IngestUpload(
            uri="file:///tmp/boom.csv",
            digest="hash",
            total_bytes=1,
            extension="csv",
        )

    def fake_enqueue(*_args, **_kwargs):
        raise ApiError(status_code=422, code="unprocessable_entity", detail="invalid")

    monkeypatch.setattr(ingest_module, "download_uri_to_temp", fake_download)
    monkeypatch.setattr(ingest_module, "enqueue_import_task", fake_enqueue)

    request = _make_request({"uri": "s3://bucket/file.csv"})
    response = await ingest_module.submit_ingest(request, file=None)
    assert response.status_code == 422
    payload = json.loads(response.body.decode())
    assert payload["error"]["code"] == "unprocessable_entity"
    assert "invalid" in payload["error"]["detail"]


@pytest.mark.asyncio
async def test_submit_ingest_logs_unexpected_error(monkeypatch):
    class DummyLogger:
        def __init__(self):
            self.exceptions = 0

        def bind(self, **_kwargs):
            return self

        def exception(self, *args, **kwargs):
            self.exceptions += 1

        def error(self, *args, **kwargs):
            self.exceptions += 1

    dummy_logger = DummyLogger()
    captured: dict[str, Exception] = {}

    def _capture(exc):
        captured["exc"] = exc

    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ingest_module, "bind_request_logger", lambda *a, **k: dummy_logger)
    monkeypatch.setattr(ingest_module.sentry_sdk, "capture_exception", _capture)
    monkeypatch.setattr(ingest_module, "enqueue_import_task", boom)
    request = _make_request({})
    upload = UploadFile(filename="data.csv", file=BytesIO(b"a,b\n1,2\n"))
    response = await ingest_module.submit_ingest(request, file=upload)
    assert response.status_code == 500
    assert "exc" in captured
    assert dummy_logger.exceptions >= 1
