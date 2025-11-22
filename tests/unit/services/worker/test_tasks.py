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


def _stub_streaming_settings(monkeypatch, *, threshold_mb: int, chunk_rows: int) -> None:
    monkeypatch.setattr(tasks_module.settings, "etl", None, raising=False)
    tasks_module.settings.__dict__.pop("etl", None)
    monkeypatch.setattr(tasks_module.settings, "INGEST_STREAMING_ENABLED", True, raising=False)
    monkeypatch.setattr(tasks_module.settings, "INGEST_STREAMING_THRESHOLD_MB", threshold_mb, raising=False)
    monkeypatch.setattr(tasks_module.settings, "INGEST_STREAMING_CHUNK_SIZE", chunk_rows, raising=False)
    monkeypatch.setattr(tasks_module.settings, "INGEST_STREAMING_CHUNK_SIZE_MB", 3, raising=False)


def _run_task_and_capture_streaming(monkeypatch, file_path: Path) -> tuple[dict, dict]:
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
        calls["streaming"] = streaming
        calls["chunk_size"] = chunk_size
        return {"rows": 1, "dialect": "returns_report", "target_table": "returns_raw"}

    monkeypatch.setattr(tasks_module, "_resolve_uri_to_path", lambda uri: file_path)
    monkeypatch.setattr("etl.load_csv.import_file", fake_import)
    monkeypatch.setattr(
        "etl.load_csv.resolve_streaming_chunk_rows", lambda chunk_size=None, chunk_size_mb=None: chunk_size
    )
    monkeypatch.setattr(tasks_module.task_import_file, "update_state", lambda *a, **k: None, raising=False)
    result = tasks_module.task_import_file.run(uri=f"file://{file_path}")
    return calls, result


def test_task_import_file_uses_legacy_mode_below_threshold(monkeypatch, tmp_path):
    target = tmp_path / "small.csv"
    target.write_bytes(b"x" * (4 * 1024 * 1024))
    _stub_streaming_settings(monkeypatch, threshold_mb=5, chunk_rows=777)

    calls, result = _run_task_and_capture_streaming(monkeypatch, target)

    assert calls["streaming"] is False
    assert calls["chunk_size"] == 777
    assert result["streaming"] is False


def test_task_import_file_streams_large_files(monkeypatch, tmp_path):
    target = tmp_path / "large.csv"
    target.write_bytes(b"x" * (6 * 1024 * 1024))
    _stub_streaming_settings(monkeypatch, threshold_mb=5, chunk_rows=888)

    calls, result = _run_task_and_capture_streaming(monkeypatch, target)

    assert calls["streaming"] is True
    assert calls["chunk_size"] == 888
    assert result["streaming"] is True
