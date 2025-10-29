import os

from services.etl import sp_fees


class DummyEngine:
    def __init__(self):
        self.disposed = False

    def dispose(self):
        self.disposed = True


def test_main_offline(monkeypatch, tmp_path):
    os.environ.pop("ENABLE_LIVE", None)
    os.environ["TESTING"] = "1"
    dummy = DummyEngine()
    monkeypatch.setattr("services.etl.sp_fees.create_engine", lambda dsn: dummy)
    captured = {}

    def fake_upsert(engine, rows, testing):
        captured["engine"] = engine
        captured["rows"] = rows
        captured["testing"] = testing

    monkeypatch.setattr(sp_fees.repo, "upsert_fees_raw", fake_upsert)
    assert sp_fees.main([]) == 0
    assert captured["engine"] is dummy
    assert captured["testing"]
    assert len(captured["rows"]) >= 1
    assert dummy.disposed
