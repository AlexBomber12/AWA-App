import os
import sys
from services.etl import sp_fees_ingestor


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


sys.modules["psycopg2"].connect = fake_connect


def test_offline(monkeypatch, tmp_path):
    os.environ["ENABLE_LIVE"] = "0"
    os.environ["SP_REFRESH_TOKEN"] = "t"
    os.environ["SP_CLIENT_ID"] = "i"
    os.environ["SP_CLIENT_SECRET"] = "s"
    os.environ["SELLER_ID"] = "seller"
    os.environ["REGION"] = "EU"
    os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "dsn")
    res = sp_fees_ingestor.main()
    assert res == 0
