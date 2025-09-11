import importlib
import os
import sys
import types

from packages.awa_common.dsn import build_dsn


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


def test_offline(monkeypatch):
    os.environ.pop("ENABLE_LIVE", None)
    os.environ["DATABASE_URL"] = build_dsn(sync=True)
    called = {"n": 0}

    def fake_get(url):
        called["n"] += 1
        return types.SimpleNamespace(json=lambda: {})

    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace(get=fake_get))
    conn = FakeConn()
    monkeypatch.setitem(
        sys.modules, "pg_utils", types.SimpleNamespace(connect=lambda dsn: conn)
    )
    helium_fees = importlib.import_module("helium_fees")

    helium_fees.main()

    assert called["n"] == 0
    inserts = [q for q in conn.cur.queries if q[0].startswith("INSERT INTO fees_raw")]
    assert len(inserts) == 2
