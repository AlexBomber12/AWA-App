from __future__ import annotations

import tempfile
from importlib import reload
from pathlib import Path


def test_task_import_file_eager(monkeypatch) -> None:
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "true")
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
    monkeypatch.setenv("CELERY_TASK_STORE_EAGER_RESULT", "true")
    import services.ingest.celery_app as celery_module
    import services.ingest.tasks as tasks_module

    reload(celery_module)
    task_import_file = reload(tasks_module).task_import_file

    tmp_dir = Path(tempfile.mkdtemp(prefix="ingest_"))
    file_path = tmp_dir / "data.csv"
    file_path.write_text("a,b\n1,2\n")

    def fake_import_file(path: str, report_type=None, celery_update=None):
        return {"rows": 1, "dialect": "returns_report", "target_table": "returns_raw"}

    monkeypatch.setattr("etl.load_csv.import_file", fake_import_file)

    res = task_import_file.delay(f"file://{file_path}")
    summary = res.get(timeout=5)

    assert summary["status"] == "success"
    assert not tmp_dir.exists()
