import os
import sys
import types
from services.common.dsn import build_dsn
from services.etl import helium_fees_ingestor


class FakeCursor:
    def __init__(self):
        self.stmts = []

    def execute(self, q, params=None):
        self.stmts.append((q, params))

    def close(self):
        pass


class FakeConn:
    def __init__(self):
        self.c = FakeCursor()

    def cursor(self):
        return self.c

    def commit(self):
        pass

    def close(self):
        pass


def fake_connect(dsn):
    return FakeConn()


sys.modules["pg_utils"] = types.SimpleNamespace(connect=fake_connect)  # type: ignore[assignment]
helium_fees_ingestor.connect = fake_connect


def test_offline(monkeypatch):
    os.environ["ENABLE_LIVE"] = "0"
    os.environ["HELIUM_API_KEY"] = "k"
    os.environ["DATABASE_URL"] = build_dsn(sync=True)
    res = helium_fees_ingestor.main()
    assert res == 0


def test_run_twice(monkeypatch):
    os.environ["ENABLE_LIVE"] = "0"
    os.environ["HELIUM_API_KEY"] = "k"
    os.environ["DATABASE_URL"] = build_dsn(sync=True)

    helium_fees_ingestor.main()
    helium_fees_ingestor.main()
