import types
from pathlib import Path

import pytest

from services.worker import tasks as tasks_module


def test_resolve_uri_to_path_file(tmp_path):
    target = tmp_path / "file.csv"
    target.write_text("data", encoding="utf-8")
    path = tasks_module._resolve_uri_to_path(f"file://{target}")
    assert path == target


def test_resolve_uri_to_path_minio(monkeypatch):
    monkeypatch.setattr(tasks_module, "_download_minio_to_tmp", lambda uri: Path("/tmp/file"))
    path = tasks_module._resolve_uri_to_path("minio://bucket/key")
    assert path == Path("/tmp/file")


def test_task_import_file_success(monkeypatch, tmp_path):
    payload = {"rows": 2}

    local = tmp_path / "data.csv"
    local.write_text("a,b\n1,2\n", encoding="utf-8")

    monkeypatch.setattr(tasks_module, "_resolve_uri_to_path", lambda uri: local)

    def fake_import(
        path, report_type=None, celery_update=None, force=False, idempotency_key=None, streaming=False, chunk_size=None
    ):
        assert "data.csv" in path
        assert streaming is False
        if celery_update:
            celery_update({"progress": 50})
        return payload

    monkeypatch.setattr("etl.load_csv.import_file", fake_import)

    class DummyShutil:
        @staticmethod
        def rmtree(*_args, **_kwargs):
            return None

    monkeypatch.setattr(tasks_module, "shutil", DummyShutil)

    updates = []

    def record_update(*args, **kwargs):
        updates.append(kwargs)

    monkeypatch.setattr(tasks_module.task_import_file, "update_state", record_update, raising=False)

    result = tasks_module.task_import_file.run(uri="file://data.csv")
    assert result["status"] == "success"
    assert any(update.get("meta", {}).get("stage") == "ingest" for update in updates)


def test_task_rebuild_views_returns_success():
    assert tasks_module.task_rebuild_views.run() == {
        "status": "success",
        "message": "noop",
    }


def test_download_minio_to_tmp_uses_shared_kwargs(monkeypatch, tmp_path):
    tmp_dir = tmp_path / "ingest_case"
    tmp_dir.mkdir()

    captured: dict[str, object] = {}

    class DummyBody:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def iter_chunks(self):
            yield b"data"

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def get_object(self, Bucket: str, Key: str):
            captured["bucket"] = Bucket
            captured["key"] = Key
            return {"Body": DummyBody()}

    class DummySession:
        def client(self, *_args, **kwargs):
            captured["endpoint_url"] = kwargs.get("endpoint_url")
            captured["aws_access_key_id"] = kwargs.get("aws_access_key_id")
            captured["aws_secret_access_key"] = kwargs.get("aws_secret_access_key")
            return DummyClient()

    monkeypatch.setattr(
        tasks_module,
        "get_s3_client_kwargs",
        lambda: {
            "endpoint_url": "https://custom:9000",
            "aws_access_key_id": "ak",
            "aws_secret_access_key": "sk",
            "region_name": "us-east-1",
        },
    )
    monkeypatch.setattr(tasks_module.tempfile, "mkdtemp", lambda prefix: str(tmp_dir))
    monkeypatch.setattr(tasks_module.aioboto3, "Session", lambda: DummySession())

    result = tasks_module._download_minio_to_tmp("minio://bucket/path/to/data.csv")

    assert result == tmp_dir / "data.csv"
    assert captured["bucket"] == "bucket"
    assert captured["key"] == "path/to/data.csv"
    assert "https://custom:9000" in captured["endpoint_url"]
    assert captured["aws_access_key_id"] == "ak"
    assert captured["aws_secret_access_key"] == "sk"


def test_task_import_file_cleans_up_on_failure(monkeypatch, tmp_path):
    tmp_dir = tmp_path / "ingest_tmp"
    tmp_dir.mkdir()
    local_path = tmp_dir / "data.csv"
    local_path.write_text("a,b", encoding="utf-8")

    monkeypatch.setattr(tasks_module, "_resolve_uri_to_path", lambda uri: local_path)

    def boom(*_args, **_kwargs):
        raise RuntimeError("ingest failed")

    monkeypatch.setattr("etl.load_csv.import_file", boom)

    removed: dict[str, Path] = {}

    def fake_rmtree(path, ignore_errors=False):
        removed["path"] = Path(path)
        removed["ignore_errors"] = ignore_errors

    monkeypatch.setattr(tasks_module, "shutil", types.SimpleNamespace(rmtree=fake_rmtree))

    updates = []

    def record_update(*_args, **kwargs):
        updates.append(kwargs)

    monkeypatch.setattr(tasks_module.task_import_file, "update_state", record_update, raising=False)

    with pytest.raises(RuntimeError, match="ingest failed"):
        tasks_module.task_import_file.run(uri="minio://bucket/data.csv")

    failure_updates = [u for u in updates if u.get("meta", {}).get("status") == "error"]
    assert failure_updates and "ingest failed" in failure_updates[-1]["meta"]["error"]
    assert removed["path"] == tmp_dir
    assert removed["ignore_errors"] is True


def test_task_import_file_forwards_force_flag(monkeypatch, tmp_path):
    local = tmp_path / "data.csv"
    local.write_text("x", encoding="utf-8")

    monkeypatch.setattr(tasks_module, "_resolve_uri_to_path", lambda uri: local)

    calls: dict[str, object] = {}

    def fake_import(
        path,
        report_type=None,
        celery_update=None,
        force=False,
        idempotency_key=None,
        streaming=False,
        chunk_size=None,
    ):
        calls["path"] = path
        calls["report_type"] = report_type
        calls["force"] = force
        calls["idempotency_key"] = idempotency_key
        return {}

    monkeypatch.setattr("etl.load_csv.import_file", fake_import)
    monkeypatch.setattr(tasks_module.task_import_file, "update_state", lambda *a, **k: None, raising=False)

    tasks_module.task_import_file.run(uri="file://data.csv", report_type="audit", force=True, idempotency_key="key123")

    assert calls["report_type"] == "audit"
    assert calls["force"] is True
    assert calls["idempotency_key"] == "key123"
    assert local.name in Path(calls["path"]).name
