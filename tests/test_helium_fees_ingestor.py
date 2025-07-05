import os
import sys
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


sys.modules["psycopg2"].connect = fake_connect  # type: ignore[attr-defined]


def test_offline(monkeypatch):
    os.environ["ENABLE_LIVE"] = "0"
    os.environ["HELIUM_API_KEY"] = "k"
    os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "dsn")
    res = helium_fees_ingestor.main()
    assert res == 0
