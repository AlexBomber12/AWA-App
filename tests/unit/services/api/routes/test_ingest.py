from io import BytesIO

import pytest
from celery import states
from fastapi import HTTPException, UploadFile
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


@pytest.mark.asyncio
async def test_submit_ingest_from_payload(monkeypatch):
    recorded = {}

    class DummyAsync:
        def __init__(self):
            self.id = "abc"

    def fake_apply_async(*args, **kwargs):
        recorded["args"] = args
        recorded["kwargs"] = kwargs
        return DummyAsync()

    monkeypatch.setattr(ingest_module.task_import_file, "apply_async", fake_apply_async)
    monkeypatch.setattr(ingest_module.celery_app.conf, "task_always_eager", False, raising=False)
    request = _make_request({"uri": "s3://bucket/file.csv", "report_type": "roi"})
    response = await ingest_module.submit_ingest(request, file=None)
    assert response["task_id"] == "abc"
    assert recorded["kwargs"]["queue"] == "ingest"


@pytest.mark.asyncio
async def test_submit_ingest_from_file(monkeypatch, tmp_path):
    recorded = {}

    class DummyAsync:
        id = "file-task"

    def fake_apply_async(*args, **kwargs):
        recorded["uri"] = kwargs.get("args", [])[0]
        return DummyAsync()

    monkeypatch.setattr(ingest_module.task_import_file, "apply_async", fake_apply_async)
    monkeypatch.setattr(ingest_module.celery_app.conf, "task_always_eager", False, raising=False)
    monkeypatch.setattr(ingest_module.tempfile, "mkdtemp", lambda prefix: str(tmp_path))

    upload = UploadFile(filename="data.csv", file=BytesIO(b"a,b\n1,2\n"))
    request = _make_request({})
    response = await ingest_module.submit_ingest(request, file=upload)
    assert response["task_id"] == "file-task"
    assert recorded["uri"].startswith("file://")


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

    request = _make_request({"uri": "s3://bucket/file.csv"})
    with pytest.raises(HTTPException) as excinfo:
        await ingest_module.submit_ingest(request, file=None)
    assert excinfo.value.status_code == 500
    assert "invalid" in excinfo.value.detail


@pytest.mark.asyncio
async def test_submit_ingest_eager_get_exception(monkeypatch):
    class DummyAsync:
        def __init__(self):
            self.id = "ok-task"
            self.info = {"status": "success"}

        def get(self, propagate=False):
            raise RuntimeError("transient")

        def failed(self):
            return False

    monkeypatch.setattr(ingest_module.task_import_file, "apply_async", lambda *a, **k: DummyAsync())
    monkeypatch.setattr(ingest_module.celery_app.conf, "task_always_eager", True, raising=False)

    request = _make_request({"uri": "s3://bucket/file.csv"})
    response = await ingest_module.submit_ingest(request, file=None)
    assert response["task_id"] == "ok-task"


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
