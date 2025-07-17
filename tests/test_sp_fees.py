import os
import sys
import types

from services.common.dsn import build_dsn


class FakeCursor:
    def __init__(self):
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def close(self):
        pass


class FakeConn:
    def __init__(self):
        self.cur = FakeCursor()

    def cursor(self):
        return self.cur

    def commit(self):
        pass

    def close(self):
        pass


class FakeSP:
    def __init__(self):
        self.calls = []

    def get_my_fees_estimate_for_sku(self, *args, **kwargs):
        self.calls.append(1)


def test_main_offline(monkeypatch):
    os.environ.pop("ENABLE_LIVE", None)
    os.environ["DATABASE_URL"] = build_dsn(sync=True)
    fake_api = FakeSP()
    monkeypatch.setitem(
        sys.modules,
        "sp_api.api",
        types.SimpleNamespace(SellingPartnerAPI=lambda: fake_api),
    )
    fake_conn = FakeConn()
    monkeypatch.setitem(
        sys.modules, "pg_utils", types.SimpleNamespace(connect=lambda dsn: fake_conn)
    )

    import importlib

    sys.path.insert(0, os.getcwd())
    sp_fees = importlib.import_module("sp_fees")

    sp_fees.main()

    assert fake_api.calls == []
    inserts = [q for q in fake_conn.cur.queries if q[0].startswith("INSERT INTO fees_raw")]
    assert len(inserts) == 2
