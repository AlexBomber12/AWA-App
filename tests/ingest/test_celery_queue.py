import os

import pytest

pytestmark = pytest.mark.integration


def test_enqueue_import_executes_eager(monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
    try:
        from services.ingest import tasks
    except Exception:
        pytest.skip("ingest tasks module not present")
    calls = {}

    def fake_import(path, **kw):
        calls["called"] = True

    monkeypatch.setattr("services.etl.load_csv.import_file", fake_import, raising=False)

    if hasattr(tasks, "enqueue_import"):
        res = tasks.enqueue_import.apply(
            kwargs={"uri": "/tmp/whatever.csv", "dialect": "test_generic"}
        )  # type: ignore
        assert res.successful()
        assert calls.get("called") is True
    else:
        pytest.skip("enqueue_import is not available")
