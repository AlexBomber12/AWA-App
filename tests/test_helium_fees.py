import os
import sys
import types

from awa_common.dsn import build_dsn

from services.etl import helium_fees


def test_offline(monkeypatch, patch_etl_session):
    os.environ.pop("ENABLE_LIVE", None)
    os.environ["DATABASE_URL"] = build_dsn(sync=True)
    engine, _, executed = patch_etl_session("services.etl.fba_fee_ingestor")
    called = {"n": 0}

    def fake_urlopen(request):
        called["n"] += 1
        return types.SimpleNamespace(__enter__=lambda self: self, __exit__=lambda *a: None)

    monkeypatch.setitem(sys.modules, "urllib.request", types.SimpleNamespace(urlopen=fake_urlopen))

    assert helium_fees.main([]) == 0
    assert called["n"] == 0
    assert engine.disposed
    inserts = [params for sql, params in executed if "INSERT INTO fees_raw" in sql]
    assert len(inserts) == 1
    assert len(inserts[0]) == 2
