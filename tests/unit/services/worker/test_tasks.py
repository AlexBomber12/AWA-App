from pathlib import Path

from services.worker import tasks as tasks_module


def test_resolve_uri_to_path_file(tmp_path):
    target = tmp_path / "file.csv"
    target.write_text("data", encoding="utf-8")
    path = tasks_module._resolve_uri_to_path(f"file://{target}")
    assert path == target


def test_resolve_uri_to_path_minio(monkeypatch):
    monkeypatch.setattr(
        tasks_module, "_download_minio_to_tmp", lambda uri: Path("/tmp/file")
    )
    path = tasks_module._resolve_uri_to_path("minio://bucket/key")
    assert path == Path("/tmp/file")


def test_task_import_file_success(monkeypatch, tmp_path):
    payload = {"rows": 2}

    local = tmp_path / "data.csv"
    local.write_text("a,b\n1,2\n", encoding="utf-8")

    monkeypatch.setattr(tasks_module, "_resolve_uri_to_path", lambda uri: local)

    def fake_import(path, report_type=None, celery_update=None, force=False):
        assert "data.csv" in path
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

    monkeypatch.setattr(
        tasks_module.task_import_file, "update_state", record_update, raising=False
    )

    result = tasks_module.task_import_file.run(uri="file://data.csv")
    assert result["status"] == "success"
    assert any(update.get("meta", {}).get("stage") == "ingest" for update in updates)


def test_task_rebuild_views_returns_success():
    assert tasks_module.task_rebuild_views.run() == {
        "status": "success",
        "message": "noop",
    }
