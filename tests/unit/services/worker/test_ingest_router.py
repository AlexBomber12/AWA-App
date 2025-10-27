from services.worker import ingest_router


def test_ingest_triggers_subprocess(monkeypatch):
    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
        called["check"] = check

    monkeypatch.setattr(ingest_router.subprocess, "run", fake_run)
    resp = ingest_router.ingest(path="reports/data.csv")
    assert resp == {"status": "ok"}
    assert "services.etl.load_csv" in called["cmd"]
