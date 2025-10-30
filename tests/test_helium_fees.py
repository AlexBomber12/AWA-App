import os
import sys
import types

from awa_common.dsn import build_dsn

from services.etl import helium_fees


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

    def fake_urlopen(request):
        called["n"] += 1
        return types.SimpleNamespace(
            __enter__=lambda self: self, __exit__=lambda *a: None
        )

    monkeypatch.setitem(
        sys.modules, "urllib.request", types.SimpleNamespace(urlopen=fake_urlopen)
    )
    conn = FakeConn()
    monkeypatch.setitem(
        sys.modules,
        "pg_utils",
        types.SimpleNamespace(connect=lambda dsn: conn),
    )
    monkeypatch.setattr(
        "services.etl.fba_fee_ingestor.connect", lambda dsn: conn, raising=False
    )

    assert helium_fees.main([]) == 0

    assert called["n"] == 0
    inserts = [q for q in conn.cur.queries if q[0].startswith("INSERT INTO fees_raw")]
    assert len(inserts) == 2
