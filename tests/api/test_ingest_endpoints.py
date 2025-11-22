from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.api.ingest_utils import IngestUpload

pytestmark = pytest.mark.integration


def _get_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "true")
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
    monkeypatch.setenv("CELERY_TASK_STORE_EAGER_RESULT", "true")
    from importlib import reload

    import services.api.main as main_module
    import services.api.routes.ingest as ingest_module
    import services.worker.celery_app as celery_module
    import services.worker.tasks as tasks_module

    reload(celery_module)
    reload(tasks_module)
    reload(ingest_module)
    app = reload(main_module).app

    return TestClient(app)


def test_ingest_file_upload(monkeypatch, tmp_path) -> None:
    def fake_import_file(
        path: str,
        report_type=None,
        celery_update=None,
        force=False,
        idempotency_key=None,
        streaming=False,
        chunk_size=None,
    ):
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
    def bad_import_file(
        path: str,
        report_type=None,
        celery_update=None,
        force=False,
        idempotency_key=None,
        streaming=False,
        chunk_size=None,
    ):
        raise RuntimeError("boom")

    monkeypatch.setattr("etl.load_csv.import_file", bad_import_file)
    with _get_client(monkeypatch) as client:
        f = tmp_path / "bad.csv"
        f.write_text("a,b\n1,2\n")

        resp = client.post("/ingest", json={"uri": f"file://{f}"})
        assert resp.status_code == 500
        assert resp.json()["error"]["detail"] == "boom"


def test_ingest_rejects_large_upload(monkeypatch) -> None:
    with _get_client(monkeypatch) as client:
        monkeypatch.setattr("services.api.ingest_utils.settings", "MAX_REQUEST_BYTES", 5, raising=False)
        resp = client.post("/ingest", files={"file": ("big.csv", b"abcdefghi")})
        assert resp.status_code == 413
        body = resp.json()
        assert body["error"]["code"] == "payload_too_large"
        assert "maximum size" in body["error"]["detail"]


def test_ingest_rejects_unsupported_extension(monkeypatch) -> None:
    with _get_client(monkeypatch) as client:
        resp = client.post("/ingest", files={"file": ("test.pdf", b"data")})
        assert resp.status_code == 400
        body = resp.json()
        assert body["error"]["code"] == "unsupported_file_format"
        assert body["error"]["hint"]


def test_upload_endpoint_still_dispatches(monkeypatch) -> None:
    class DummyAsync:
        id = "task-xyz"

    def fake_upload(_file, request, log=None):
        return IngestUpload(
            uri="minio://bucket/raw/amazon/key.csv",
            digest="digest",
            total_bytes=5,
            extension="csv",
            object_key="raw/amazon/key.csv",
        )

    def fake_enqueue(upload_target, *, report_type=None, force=False, log=None):
        return DummyAsync()

    with _get_client(monkeypatch) as client:
        monkeypatch.setattr("services.api.routes.upload.upload_file_to_minio", fake_upload)
        monkeypatch.setattr("services.api.routes.upload.enqueue_import_task", fake_enqueue)
        resp = client.post("/upload", files={"file": ("data.csv", b"a,b\n1,2\n")})
        assert resp.status_code == 202
        body = resp.json()
        assert body["task_id"] == "task-xyz"
        assert body["idempotency_key"] == "digest"
