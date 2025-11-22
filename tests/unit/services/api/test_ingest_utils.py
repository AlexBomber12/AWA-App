from __future__ import annotations

import hashlib
import shutil
from io import BytesIO

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


def test_ensure_size_limit_raises_payload_too_large():
    request = Request({"type": "http", "headers": [(b"content-length", b"1024")]})
    with pytest.raises(ApiError) as excinfo:
        ingest_utils.ensure_size_limit(request, max_bytes=100)
    assert excinfo.value.code == "payload_too_large"


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
