from __future__ import annotations

import types

import pytest

from services.worker import tasks


@pytest.mark.asyncio
async def test_download_minio_async(monkeypatch, tmp_path) -> None:
    tmpdir = tmp_path / "minio"
    tmpdir.mkdir()

    class DummyBody:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def iter_chunks(self):
            yield b"chunk"

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get_object(self, Bucket, Key):
            return {"Body": DummyBody()}

    class DummySession:
        def client(self, *args, **kwargs):
            return DummyClient()

    monkeypatch.setattr(tasks, "aioboto3", types.SimpleNamespace(Session=lambda: DummySession()))
    monkeypatch.setattr(tasks, "get_s3_client_kwargs", lambda: {"endpoint_url": "http://minio"}, raising=False)
    monkeypatch.setattr(tasks, "get_s3_client_config", lambda: "cfg", raising=False)
    path = await tasks._download_minio_async("minio://bucket/path/file.txt")
    assert path.exists()
    assert path.read_bytes() == b"chunk"
