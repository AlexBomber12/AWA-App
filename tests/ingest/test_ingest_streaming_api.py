from __future__ import annotations

from importlib import reload
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

pytestmark = pytest.mark.integration


def _make_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "true")
    monkeypatch.setenv("BROKER_URL", "memory://")
    monkeypatch.setenv("RESULT_BACKEND", "cache+memory://")
    monkeypatch.setenv("CELERY_TASK_STORE_EAGER_RESULT", "true")
    monkeypatch.setenv("INGEST_STREAMING_ENABLED", "1")
    monkeypatch.setenv("INGEST_STREAMING_THRESHOLD_MB", "1")
    monkeypatch.setenv("INGEST_STREAMING_CHUNK_SIZE_MB", "1")
    monkeypatch.setenv("ANALYZE_MIN_ROWS", "999999")

    import etl.load_csv as load_csv
    from awa_common.settings import settings

    settings.__dict__.pop("etl", None)
    settings.__dict__.pop("ingestion", None)
    monkeypatch.setattr(settings, "INGEST_STREAMING_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "INGEST_STREAMING_THRESHOLD_MB", 1, raising=False)
    monkeypatch.setattr(settings, "INGEST_STREAMING_CHUNK_SIZE_MB", 1, raising=False)
    monkeypatch.setattr(settings, "ANALYZE_MIN_ROWS", 999_999, raising=False)
    reload(load_csv)

    import services.api.main as main_module
    import services.worker.celery_app as celery_module
    import services.worker.tasks as tasks_module

    reload(celery_module)
    reload(tasks_module)
    app = reload(main_module).app
    return TestClient(app)


def _write_large_csv(path: Path, rows: int = 20_000) -> int:
    header = "asin,qty,refund_amount,return_reason,return_date,currency"
    filler = "reason" * 40  # add heft per row to trigger streaming threshold quickly
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"{header}\n")
        for i in range(rows):
            handle.write(f"ASIN{i:05d},1,2.5,{filler},2024-01-01,USD\n")
    return rows


def test_ingest_large_file_streams(monkeypatch, tmp_path, pg_engine) -> None:
    from awa_common.settings import settings

    monkeypatch.setenv("DATABASE_URL", str(pg_engine.url))
    monkeypatch.setattr(settings, "DATABASE_URL", str(pg_engine.url), raising=False)
    settings.__dict__.pop("etl", None)
    with _make_client(monkeypatch) as client:
        payload = tmp_path / "returns.csv"
        expected_rows = _write_large_csv(payload)
        assert payload.stat().st_size > 1_000_000  # ensure we cross the configured 1 MB threshold

        with pg_engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE returns_raw"))
            conn.execute(text("TRUNCATE TABLE load_log"))

        resp = client.post("/ingest", json={"uri": f"file://{payload}"})
        assert resp.status_code == 200
        task_id = resp.json()["task_id"]

        job = client.get(f"/jobs/{task_id}")
        assert job.status_code == 200
        body = job.json()
        assert body["state"] == "SUCCESS"
        assert body["meta"].get("streaming") is True
        assert int(body["meta"].get("streaming_chunk_size_mb", 0)) == 1

    with pg_engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM returns_raw")).scalar_one()
        log_row = conn.execute(
            text("SELECT payload_meta FROM load_log WHERE source='ingest.import_file' ORDER BY id DESC LIMIT 1")
        ).scalar_one()

    assert count == expected_rows
    assert log_row.get("streaming") is True
    assert int(log_row.get("streaming_chunk_size_mb", 0)) == 1
