from __future__ import annotations

import hashlib
import shutil
from io import BytesIO

import httpx
import pytest
from fastapi import UploadFile
from starlette.requests import Request

from services.api import ingest_utils
from services.api.ingest_utils import ApiError, IngestUpload


def test_validate_upload_file_rejects_extension():
    upload = UploadFile(filename="notes.txt", file=BytesIO(b"abc"))
    with pytest.raises(ApiError) as excinfo:
        ingest_utils.validate_upload_file(upload)
    assert excinfo.value.code == "unsupported_file_format"


def test_validate_upload_file_accepts_string_name():
    safe_name, ext = ingest_utils.validate_upload_file("Report.CSV")
    assert safe_name.endswith(".csv")
    assert ext == "csv"


def test_ensure_size_limit_raises_payload_too_large():
    request = Request({"type": "http", "headers": [(b"content-length", b"1024")]})
    with pytest.raises(ApiError) as excinfo:
        ingest_utils.ensure_size_limit(request, max_bytes=100)
    assert excinfo.value.code == "payload_too_large"


def test_ensure_size_limit_ignores_invalid_header():
    request = Request({"type": "http", "headers": [(b"content-length", b"bad")]})
    ingest_utils.ensure_size_limit(request, max_bytes=1)


@pytest.mark.asyncio
async def test_persist_upload_tracks_digest_and_total(monkeypatch):
    upload = UploadFile(filename="data.csv", file=BytesIO(b"a,b\n1,2\n"))
    request = Request({"type": "http", "headers": []})
    monkeypatch.setattr(ingest_utils.settings, "MAX_REQUEST_BYTES", 1024)
    result = await ingest_utils.persist_upload_to_temp(upload, request=request, log=ingest_utils.logger)
    assert result.total_bytes == len(b"a,b\n1,2\n")
    assert result.digest == hashlib.sha256(b"a,b\n1,2\n").hexdigest()
    assert result.uri.startswith("file://")
    if result.path:
        shutil.rmtree(result.path.parent, ignore_errors=True)


def test_enqueue_import_task_uses_ingest_queue(monkeypatch):
    recorded = {}

    class DummyAsync:
        def __init__(self):
            self.id = "task-1"
            self.info = {}

        def get(self, propagate=True):
            return None

        def failed(self):
            return False

    def fake_apply_async(*args, **kwargs):
        recorded["args"] = args
        recorded["kwargs"] = kwargs
        return DummyAsync()

    upload = IngestUpload(uri="file:///tmp/data.csv", digest="hash", total_bytes=1, extension="csv")
    monkeypatch.setattr(ingest_utils.task_import_file, "apply_async", fake_apply_async)
    monkeypatch.setattr(ingest_utils.celery_app.conf, "task_always_eager", False, raising=False)

    result = ingest_utils.enqueue_import_task(upload, report_type="roi", force=True, log=ingest_utils.logger)
    assert recorded["kwargs"]["queue"] == "ingest"
    assert recorded["kwargs"]["kwargs"]["idempotency_key"] == "hash"
    assert recorded["kwargs"]["kwargs"]["report_type"] == "roi"
    assert recorded["kwargs"]["kwargs"]["force"] is True
    assert result.id == "task-1"


@pytest.mark.asyncio
async def test_upload_file_to_minio_builds_uri(monkeypatch):
    class DummyClient:
        def __init__(self):
            self.put_calls = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def put_object(self, Bucket, Key, Body):
            self.put_calls.append((Bucket, Key, Body))

        async def create_multipart_upload(self, Bucket, Key):
            return {"UploadId": "upload-1"}

        async def upload_part(self, Bucket, Key, UploadId, PartNumber, Body):
            return {"ETag": "etag"}

        async def complete_multipart_upload(self, Bucket, Key, UploadId, MultipartUpload):
            return {"ok": True}

        async def abort_multipart_upload(self, Bucket, Key, UploadId):
            self.put_calls.append(("aborted", Key, UploadId))

    class DummySession:
        def __init__(self, client):
            self.client_obj = client

        def client(self, *_args, **_kwargs):
            return self.client_obj

    dummy_client = DummyClient()
    monkeypatch.setattr(ingest_utils.aioboto3, "Session", lambda: DummySession(dummy_client))
    monkeypatch.setattr(ingest_utils, "get_bucket_name", lambda: "test-bucket")
    monkeypatch.setattr(ingest_utils.settings, "MAX_REQUEST_BYTES", 1024)
    monkeypatch.setattr(ingest_utils.settings, "INGEST_CHUNK_SIZE_MB", 1)

    upload = UploadFile(filename="report.csv", file=BytesIO(b"a,b\n1,2\n"))
    request = Request({"type": "http", "headers": []})
    result = await ingest_utils.upload_file_to_minio(upload, request=request, log=ingest_utils.logger)
    assert result.uri.startswith("minio://test-bucket/")
    assert result.object_key
    assert result.digest == hashlib.sha256(b"a,b\n1,2\n").hexdigest()
    assert dummy_client.put_calls


@pytest.mark.asyncio
async def test_download_uri_to_temp_rejects_unknown_scheme():
    with pytest.raises(ApiError):
        await ingest_utils.download_uri_to_temp("ftp://example.com/path", log=ingest_utils.logger)


def test_validate_upload_file_missing_name():
    upload = UploadFile(filename=None, file=BytesIO(b""))
    with pytest.raises(ApiError):
        ingest_utils.validate_upload_file(upload)


def test_validate_upload_file_rejects_after_sanitize(monkeypatch):
    upload = UploadFile(filename="payload.bad", file=BytesIO(b"content"))

    def fake_sanitize(_name):
        return "payload.bad"

    monkeypatch.setattr(ingest_utils, "sanitize_upload_name", fake_sanitize)
    with pytest.raises(ApiError) as excinfo:
        ingest_utils.validate_upload_file(upload)
    assert excinfo.value.code == "unsupported_file_format"
    assert excinfo.value.hint


def test_api_error_response_sets_header(monkeypatch):
    request = Request({"type": "http", "path": "/ingest", "headers": []})
    error = ApiError(status_code=400, code="bad_request", detail="oops", hint="fix")
    calls = {}
    monkeypatch.setattr(ingest_utils, "record_api_ingest_4xx_total", lambda code: calls.setdefault("code", code))
    monkeypatch.setattr(ingest_utils, "get_request_id", lambda _r: "req-1")

    resp = ingest_utils.api_error_response(request, error, route="/ingest")
    body = resp.body.decode()
    assert '"bad_request"' in body
    assert resp.headers["X-Request-ID"] == "req-1"
    assert calls["code"] == "bad_request"


def test_api_error_response_records_5xx(monkeypatch):
    request = Request({"type": "http", "path": "/ingest", "headers": []})
    error = ApiError(status_code=500, code="bad_request", detail="boom")
    calls = {}
    monkeypatch.setattr(ingest_utils, "record_api_ingest_5xx_total", lambda: calls.setdefault("five", True))
    resp = ingest_utils.api_error_response(request, error, route="/ingest")
    assert resp.status_code == 500
    assert calls["five"] is True


def test_enqueue_import_task_eager_failure(monkeypatch):
    class DummyAsync:
        def __init__(self):
            self.id = "task-1"
            self.info = ingest_utils.ImportFileError("invalid")

        def get(self, propagate=True):
            raise RuntimeError("boom")

        def failed(self):
            return True

    def fake_apply_async(*_a, **_k):
        return DummyAsync()

    monkeypatch.setattr(ingest_utils.task_import_file, "apply_async", fake_apply_async)
    monkeypatch.setattr(ingest_utils.celery_app.conf, "task_always_eager", True, raising=False)

    upload = IngestUpload(uri="file:///tmp/x.csv", digest="hash", total_bytes=1, extension="csv")
    with pytest.raises(ApiError):
        ingest_utils.enqueue_import_task(upload, report_type=None, force=False, log=ingest_utils.logger)


def test_route_path_and_bind_logger(monkeypatch):
    class DummyReq:
        def __init__(self):
            self.scope = {"path": ""}
            self.url = None

    request = DummyReq()
    assert ingest_utils.route_path(request) == "/"
    monkeypatch.setattr(ingest_utils, "get_request_id", lambda _r: "req-123")
    logger = ingest_utils.bind_request_logger(request, ingest_source="upload")
    bound = logger.bind(test="ok")
    assert bound


def test_validate_upload_file_bad_request(monkeypatch):
    upload = UploadFile(filename="data.csv", file=BytesIO(b"abc"))

    def boom(_name):
        raise ValueError("boom")

    monkeypatch.setattr(ingest_utils, "sanitize_upload_name", boom)
    with pytest.raises(ApiError) as excinfo:
        ingest_utils.validate_upload_file(upload)
    assert excinfo.value.code == "bad_request"


@pytest.mark.asyncio
async def test_persist_upload_to_temp_enforces_limit(monkeypatch):
    upload = UploadFile(filename="data.csv", file=BytesIO(b"too large"))
    request = Request({"type": "http", "headers": []})
    monkeypatch.setattr(ingest_utils.settings, "MAX_REQUEST_BYTES", 1)
    with pytest.raises(ApiError) as excinfo:
        await ingest_utils.persist_upload_to_temp(upload, request=request, log=ingest_utils.logger)
    assert excinfo.value.code == "payload_too_large"


@pytest.mark.asyncio
async def test_upload_file_to_minio_enforces_limit(monkeypatch):
    upload = UploadFile(filename="data.csv", file=BytesIO(b"0123456789"))
    request = Request({"type": "http", "headers": []})
    monkeypatch.setattr(ingest_utils.settings, "MAX_REQUEST_BYTES", 5)
    monkeypatch.setattr(ingest_utils.settings, "INGEST_CHUNK_SIZE_MB", 1)
    failures = {}
    monkeypatch.setattr(
        ingest_utils,
        "record_ingest_upload_failure",
        lambda extension, reason: failures.setdefault("reason", reason),
    )

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def put_object(self, **_k):
            return None

        async def create_multipart_upload(self, **_k):
            return {"UploadId": "u"}

        async def upload_part(self, **_k):
            return {"ETag": "etag"}

        async def complete_multipart_upload(self, **_k):
            return None

        async def abort_multipart_upload(self, **_k):
            return None

    class DummySession:
        def client(self, *_a, **_k):
            return DummyClient()

    monkeypatch.setattr(ingest_utils.aioboto3, "Session", lambda: DummySession())
    with pytest.raises(ApiError) as excinfo:
        await ingest_utils.upload_file_to_minio(upload, request=request, log=ingest_utils.logger)
    assert excinfo.value.code == "payload_too_large"
    assert failures["reason"] == "payload_too_large"


@pytest.mark.asyncio
async def test_persist_upload_records_failure_on_exception(monkeypatch):
    class BoomUpload(UploadFile):
        async def read(self, *_a, **_k):
            raise RuntimeError("boom")

    upload = BoomUpload(filename="data.csv", file=BytesIO(b"abc"))
    request = Request({"type": "http", "headers": []})
    failures = {}
    monkeypatch.setattr(
        ingest_utils, "record_ingest_upload_failure", lambda extension, reason: failures.setdefault("reason", reason)
    )
    monkeypatch.setattr(ingest_utils.settings, "MAX_REQUEST_BYTES", 1024)
    with pytest.raises(RuntimeError):
        await ingest_utils.persist_upload_to_temp(upload, request=request, log=ingest_utils.logger)
    assert failures["reason"] == "RuntimeError"


@pytest.mark.asyncio
async def test_download_file_enforces_limit(monkeypatch, tmp_path):
    target = tmp_path / "big.csv"
    target.write_bytes(b"0123456789")
    monkeypatch.setattr(ingest_utils.settings, "MAX_REQUEST_BYTES", 5)
    with pytest.raises(ApiError) as excinfo:
        await ingest_utils.download_uri_to_temp(f"file://{target}", log=ingest_utils.logger)
    assert excinfo.value.code == "payload_too_large"


@pytest.mark.asyncio
async def test_write_stream_to_temp_too_large(monkeypatch):
    async def gen():
        yield b"0123456789"

    monkeypatch.setattr(ingest_utils.settings, "MAX_REQUEST_BYTES", 5)
    with pytest.raises(ApiError):
        await ingest_utils._write_stream_to_temp(gen(), scheme="http")


def test_error_from_failure_maps_import_validation(monkeypatch):
    err = ingest_utils.ImportFileError("invalid")
    err.status_code = 422
    api_err = ingest_utils._error_from_failure(err)
    assert api_err.code == "unprocessable_entity"


@pytest.mark.asyncio
async def test_download_file_success(monkeypatch, tmp_path):
    target = tmp_path / "small.csv"
    target.write_bytes(b"a,b\n1,2\n")
    monkeypatch.setattr(ingest_utils.settings, "MAX_REQUEST_BYTES", 1024)
    result = await ingest_utils.download_uri_to_temp(f"file://{target}", log=ingest_utils.logger)
    assert result.total_bytes == target.stat().st_size
    assert result.digest == hashlib.sha256(target.read_bytes()).hexdigest()


@pytest.mark.asyncio
async def test_download_minio_success(monkeypatch):
    calls = {}

    class DummyBody:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def iter_chunks(self):
            calls.setdefault("iter", True)
            yield b"abc"

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get_object(self, Bucket, Key):
            calls["bucket"] = Bucket
            calls["key"] = Key
            return {"Body": DummyBody()}

    class DummySession:
        def client(self, *_a, **_k):
            return DummyClient()

    monkeypatch.setattr(ingest_utils.aioboto3, "Session", lambda: DummySession())
    monkeypatch.setattr(ingest_utils, "get_s3_client_config", lambda: None)
    monkeypatch.setattr(ingest_utils, "get_s3_client_kwargs", lambda: {})
    monkeypatch.setattr(ingest_utils.settings, "MAX_REQUEST_BYTES", 1024)

    result = await ingest_utils.download_uri_to_temp("minio://bucket/object.csv", log=ingest_utils.logger)
    assert result.uri.startswith("file://")
    assert calls["bucket"] == "bucket"
    assert calls["key"] == "object.csv"


@pytest.mark.asyncio
async def test_download_minio_failure(monkeypatch):
    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get_object(self, Bucket, Key):
            raise RuntimeError("fail")

    class DummySession:
        def client(self, *_a, **_k):
            return DummyClient()

    monkeypatch.setattr(ingest_utils.aioboto3, "Session", lambda: DummySession())
    monkeypatch.setattr(ingest_utils, "get_s3_client_config", lambda: None)
    monkeypatch.setattr(ingest_utils, "get_s3_client_kwargs", lambda: {})
    with pytest.raises(ApiError):
        await ingest_utils.download_uri_to_temp("minio://bucket/object.csv", log=ingest_utils.logger)


@pytest.mark.asyncio
async def test_download_http_success(monkeypatch):
    class DummyResponse:
        def __init__(self):
            self.closed = False

        async def aiter_bytes(self, chunk_size):
            yield b"abc"

        async def aclose(self):
            self.closed = True

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def request(self, *_a, **_k):
            return DummyResponse()

    monkeypatch.setattr(ingest_utils, "AsyncHTTPClient", lambda *a, **k: DummyClient())
    monkeypatch.setattr(ingest_utils.settings, "MAX_REQUEST_BYTES", 1024)
    result = await ingest_utils.download_uri_to_temp("http://example.com/file.csv", log=ingest_utils.logger)
    assert result.uri.startswith("file://")


@pytest.mark.asyncio
async def test_download_http_status_error(monkeypatch):
    class DummyResponse(httpx.Response):
        def __init__(self):
            super().__init__(status_code=503)

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def request(self, *_a, **_k):
            raise httpx.HTTPStatusError("bad", request=None, response=DummyResponse())

    failures = {}
    monkeypatch.setattr(ingest_utils, "AsyncHTTPClient", lambda *a, **k: DummyClient())
    monkeypatch.setattr(
        ingest_utils, "record_ingest_download_failure", lambda scheme, reason: failures.setdefault("reason", reason)
    )
    with pytest.raises(ApiError):
        await ingest_utils.download_uri_to_temp("http://example.com/file.csv", log=ingest_utils.logger)
    assert failures["reason"] == "503"


@pytest.mark.asyncio
async def test_download_http_timeout(monkeypatch):
    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def request(self, *_a, **_k):
            raise httpx.TimeoutException("timeout")

    failures = {}
    monkeypatch.setattr(ingest_utils, "AsyncHTTPClient", lambda *a, **k: DummyClient())
    monkeypatch.setattr(
        ingest_utils, "record_ingest_download_failure", lambda scheme, reason: failures.setdefault("reason", reason)
    )
    with pytest.raises(ApiError) as excinfo:
        await ingest_utils.download_uri_to_temp("http://example.com/file.csv", log=ingest_utils.logger)
    assert excinfo.value.status_code == 504
    assert failures["reason"] == "timeout"
