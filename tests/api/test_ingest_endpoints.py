from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def _get_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "true")
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
    monkeypatch.setenv("CELERY_TASK_STORE_EAGER_RESULT", "true")
    from importlib import reload

    import api.routers.ingest as ingest_module
    import services.api.main as main_module
    import services.ingest.celery_app as celery_module
    import services.ingest.tasks as tasks_module

    reload(celery_module)
    reload(tasks_module)
    reload(ingest_module)
    app = reload(main_module).app

    return TestClient(app)


def test_ingest_file_upload(monkeypatch, tmp_path) -> None:
    def fake_import_file(path: str, report_type=None, celery_update=None, force=False):
        return {"rows": 2, "dialect": "returns_report", "target_table": "returns_raw"}

    monkeypatch.setattr("etl.load_csv.import_file", fake_import_file)
    with _get_client(monkeypatch) as client:
        resp = client.post("/ingest", files={"file": ("test.csv", b"a,b\n1,2\n")})
        assert resp.status_code == 200
        task_id = resp.json()["task_id"]

        res = client.get(f"/jobs/{task_id}")
        assert res.status_code == 200
        body = res.json()
        assert body["state"] == "SUCCESS"
        assert body["meta"]["rows"] == 2
        assert body["meta"]["dialect"] == "returns_report"


def test_ingest_json_uri(monkeypatch, tmp_path) -> None:
    def fake_import_file(path: str, report_type=None, celery_update=None, force=False):
        return {"rows": 1, "dialect": "returns_report", "target_table": "returns_raw"}

    monkeypatch.setattr("etl.load_csv.import_file", fake_import_file)
    with _get_client(monkeypatch) as client:
        f = tmp_path / "sample.csv"
        f.write_text("a,b\n1,2\n")

        resp = client.post("/ingest", json={"uri": f"file://{f}"})
        assert resp.status_code == 200
        task_id = resp.json()["task_id"]

        res = client.get(f"/jobs/{task_id}")
        assert res.status_code == 200
        assert res.json()["state"] == "SUCCESS"


def test_ingest_failure(monkeypatch, tmp_path) -> None:
    def bad_import_file(path: str, report_type=None, celery_update=None, force=False):
        raise RuntimeError("boom")

    monkeypatch.setattr("etl.load_csv.import_file", bad_import_file)
    with _get_client(monkeypatch) as client:
        from services.ingest.celery_app import celery_app

        celery_app.conf.task_eager_propagates = False

        f = tmp_path / "bad.csv"
        f.write_text("a,b\n1,2\n")

        resp = client.post("/ingest", json={"uri": f"file://{f}"})
        assert resp.status_code == 200
        task_id = resp.json()["task_id"]

        res = client.get(f"/jobs/{task_id}")
        assert res.status_code == 200
        body = res.json()
        assert body["state"] == "FAILURE"
        assert body["meta"]["status"] == "error"
