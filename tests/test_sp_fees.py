import os

import pytest

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


def test_sp_fees_skips_duplicate(monkeypatch, patch_etl_session, stub_load_log):
    os.environ.pop("ENABLE_LIVE", None)
    engine, _, _ = patch_etl_session("services.etl.sp_fees")
    monkeypatch.setattr(sp_fees.repo, "upsert_fees_raw", lambda *a, **k: None)

    sp_fees.main([])
    statuses_first = {record["status"] for record in stub_load_log.values()}
    assert "success" in statuses_first

    sp_fees.main([])
    statuses_second = {record["status"] for record in stub_load_log.values()}
    assert "skipped" in statuses_second
    assert engine.disposed


def test_sp_fees_failure_marks_load_log(monkeypatch, patch_etl_session, stub_load_log):
    os.environ.pop("ENABLE_LIVE", None)
    patch_etl_session("services.etl.sp_fees")

    def boom(_path):
        raise RuntimeError("boom")

    monkeypatch.setattr(sp_fees, "build_rows_from_fixture", boom)
    with pytest.raises(RuntimeError):
        sp_fees.main([])
    statuses = {record["status"] for record in stub_load_log.values()}
    assert "failed" in statuses
