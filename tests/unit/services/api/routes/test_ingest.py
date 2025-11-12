import json
from io import BytesIO

import pytest
from celery import states
from fastapi import UploadFile
from starlette.requests import Request

from etl.load_csv import ImportFileError
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

    def fake_apply_async(*args, **kwargs):
        recorded["args"] = args
        recorded["kwargs"] = kwargs
        return DummyAsync()

    remote_file = tmp_path / "remote.csv"
    remote_file.write_text("a,b", encoding="utf-8")

    async def fake_remote(uri: str):
        return remote_file, "hash-1"

    monkeypatch.setattr(ingest_module, "_download_remote", fake_remote)
    monkeypatch.setattr(ingest_module.task_import_file, "apply_async", fake_apply_async)
    monkeypatch.setattr(ingest_module.celery_app.conf, "task_always_eager", False, raising=False)
    request = _make_request({"uri": "s3://bucket/file.csv", "report_type": "roi"})
    response = await ingest_module.submit_ingest(request, file=None)
    data = _json_body(response)
    assert data["task_id"] == "abc"
    assert recorded["kwargs"]["queue"] == "ingest"
    assert recorded["kwargs"]["kwargs"]["idempotency_key"] == "hash-1"


@pytest.mark.asyncio
async def test_submit_ingest_from_file(monkeypatch, tmp_path):
    recorded = {}

    class DummyAsync:
        id = "file-task"

    def fake_apply_async(*args, **kwargs):
        recorded["kwargs"] = kwargs
        return DummyAsync()

    monkeypatch.setattr(ingest_module.task_import_file, "apply_async", fake_apply_async)
    monkeypatch.setattr(ingest_module.celery_app.conf, "task_always_eager", False, raising=False)
    monkeypatch.setattr(ingest_module.tempfile, "mkdtemp", lambda prefix: str(tmp_path))

    upload = UploadFile(filename="data.csv", file=BytesIO(b"a,b\n1,2\n"))
    request = _make_request({})
    response = await ingest_module.submit_ingest(request, file=upload)
    data = _json_body(response)
    assert data["task_id"] == "file-task"
    assert recorded["kwargs"]["args"][0].startswith("file://")
    assert recorded["kwargs"]["kwargs"]["idempotency_key"]


@pytest.mark.asyncio
async def test_get_job_returns_meta_async(monkeypatch):
    def fake_async_result(task_id):
        return DummyAsyncResult(state="FAILURE", info={})

    monkeypatch.setattr(ingest_module.celery_app, "AsyncResult", fake_async_result)
    result = await ingest_module.get_job("abc")
    assert result["state"] == "FAILURE"
    assert result["meta"]["status"] == "error"


@pytest.mark.asyncio
async def test_submit_ingest_eager_failure_propagates(monkeypatch, tmp_path):
    class DummyAsync:
        def __init__(self):
            self.id = "boom-task"
            self.info = ImportFileError("invalid")

        def get(self, propagate=False):
            return None

        def failed(self):
            return True

    def fake_apply_async(*args, **kwargs):
        return DummyAsync()

    monkeypatch.setattr(ingest_module.task_import_file, "apply_async", fake_apply_async)
    monkeypatch.setattr(ingest_module.celery_app.conf, "task_always_eager", True, raising=False)
    remote = tmp_path / "boom.csv"
    remote.write_text("a", encoding="utf-8")

    async def fake_download(_uri: str):
        return remote, "hash"

    monkeypatch.setattr(ingest_module, "_download_remote", fake_download)

    request = _make_request({"uri": "s3://bucket/file.csv"})
    response = await ingest_module.submit_ingest(request, file=None)
    assert response.status_code == 500
    payload = json.loads(response.body.decode())
    assert payload["code"] == "bad_request"
    assert "invalid" in payload["detail"]


@pytest.mark.asyncio
async def test_submit_ingest_eager_get_exception(monkeypatch, tmp_path):
    class DummyAsync:
        def __init__(self):
            self.id = "ok-task"
            self.info = {"status": "success"}

        def get(self, propagate=False):
            raise RuntimeError("transient")

        def failed(self):
            return False

    remote = tmp_path / "ok.csv"
    remote.write_text("a", encoding="utf-8")

    async def fake_download(_uri: str):
        return remote, "hash"

    monkeypatch.setattr(ingest_module, "_download_remote", fake_download)
    monkeypatch.setattr(ingest_module.task_import_file, "apply_async", lambda *a, **k: DummyAsync())
    monkeypatch.setattr(ingest_module.celery_app.conf, "task_always_eager", True, raising=False)

    request = _make_request({"uri": "s3://bucket/file.csv"})
    response = await ingest_module.submit_ingest(request, file=None)
    data = _json_body(response)
    assert data["task_id"] == "ok-task"


def test_failure_status_handles_generic_exception():
    status, detail = ingest_module._failure_status_and_detail(ValueError("oops"))
    assert status == 500
    assert detail == "oops"


def test_failure_status_handles_unknown_type():
    status, detail = ingest_module._failure_status_and_detail(None)
    assert status == 500
    assert detail == "ETL ingest failed"


def test_meta_from_result_returns_dict_for_success():
    info = {"status": "success"}
    result = ingest_module._meta_from_result(states.SUCCESS, info)
    assert result is info


def test_meta_from_result_handles_non_failure_empty():
    meta = ingest_module._meta_from_result(states.SUCCESS, None)
    assert meta == {}


def test_s3_client_kwargs_reads_env(monkeypatch):
    monkeypatch.setenv("MINIO_ENDPOINT", "custom:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "ak")
    monkeypatch.setenv("MINIO_SECRET_KEY", "sk")
    result = ingest_module._s3_client_kwargs()
    assert result["endpoint_url"] == "http://custom:9000"
    assert result["aws_access_key_id"] == "ak"
    assert result["aws_secret_access_key"] == "sk"


@pytest.mark.asyncio
async def test_persist_upload_enforces_header(monkeypatch):
    upload = UploadFile(filename="data.csv", file=BytesIO(b"a,b\n1,2\n"))
    request = Request({"type": "http", "headers": [(b"content-length", b"5")]})
    monkeypatch.setattr(ingest_module.settings, "MAX_REQUEST_BYTES", 1)
    with pytest.raises(ingest_module.IngestRequestError):
        await ingest_module._persist_upload(upload, request)


@pytest.mark.asyncio
async def test_download_remote_rejects_unknown_scheme():
    with pytest.raises(ingest_module.IngestRequestError):
        await ingest_module._download_remote("ftp://example.com/path")


@pytest.mark.asyncio
async def test_persist_upload_rejects_absolute(tmp_path):
    upload = UploadFile(filename="/tmp/data.csv", file=BytesIO(b"a,b\n1,2\n"))
    request = Request({"type": "http", "headers": []})
    with pytest.raises(ingest_module.IngestRequestError):
        await ingest_module._persist_upload(upload, request)
