import os

from services.etl import sp_fees


def test_main_offline(monkeypatch, patch_etl_session):
    os.environ.pop("ENABLE_LIVE", None)
    os.environ["TESTING"] = "1"
    engine, _, _ = patch_etl_session("services.etl.sp_fees")
    captured = {}

    def fake_upsert(engine_obj, rows, testing):
        captured["engine"] = engine_obj
        captured["rows"] = rows
        captured["testing"] = testing

    monkeypatch.setattr(sp_fees.repo, "upsert_fees_raw", fake_upsert)
    assert sp_fees.main([]) == 0
    assert captured["engine"] is engine
    assert captured["testing"]
    assert len(captured["rows"]) >= 1
    assert engine.disposed
