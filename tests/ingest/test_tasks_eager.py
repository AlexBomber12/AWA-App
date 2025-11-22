from __future__ import annotations

import tempfile
from importlib import reload
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


def test_task_import_file_eager(monkeypatch) -> None:
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "true")
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
    monkeypatch.setenv("CELERY_TASK_STORE_EAGER_RESULT", "true")
    import services.worker.celery_app as celery_module
    import services.worker.tasks as tasks_module

    reload(celery_module)
    task_import_file = reload(tasks_module).task_import_file

    tmp_dir = Path(tempfile.mkdtemp(prefix="ingest_"))
    file_path = tmp_dir / "data.csv"
    file_path.write_text("a,b\n1,2\n")

    def fake_import_file(
        path: str,
        report_type=None,
        celery_update=None,
        force=False,
        idempotency_key=None,
        streaming=False,
        chunk_size=None,
    ):
        return {"rows": 1, "dialect": "returns_report", "target_table": "returns_raw"}

    monkeypatch.setattr("etl.load_csv.import_file", fake_import_file)

    res = task_import_file.delay(f"file://{file_path}")
    summary = res.get(timeout=5)

    assert summary["status"] == "success"
    assert not tmp_dir.exists()


def test_task_import_file_failure_records_metrics(monkeypatch, tmp_path: Path) -> None:
    import services.worker.tasks as tasks_module

    file_path = tmp_path / "data.csv"
    file_path.write_text("a,b\n1,2\n", encoding="utf-8")

    def fake_resolve(uri: str) -> Path:
        return file_path

    monkeypatch.setattr(tasks_module, "_resolve_uri_to_path", fake_resolve)

    def boom(path: str, **_kwargs):
        raise RuntimeError("ingest failed")

    monkeypatch.setattr("etl.load_csv.import_file", boom)

    state: dict[str, Any] = {}
    outcomes: list[tuple[str, bool]] = []
    failures: list[Exception] = []

    monkeypatch.setattr(
        tasks_module,
        "record_ingest_task_outcome",
        lambda task, *, success, duration_s: outcomes.append((task, success)),
    )
    monkeypatch.setattr(
        tasks_module,
        "record_ingest_task_failure",
        lambda task, exc: failures.append(exc),
    )

    self = SimpleNamespace(request=SimpleNamespace(id="task-err"), update_state=lambda **kwargs: state.update(kwargs))
    inner = tasks_module.task_import_file.__wrapped__.__wrapped__
    with pytest.raises(RuntimeError):
        inner(self, uri="file://tmp/path.csv")
    assert failures, "expected failure metric"
    assert outcomes and outcomes[0] == ("ingest.import_file", False)
