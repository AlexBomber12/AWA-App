import os, types, sys

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

sys.modules['psycopg2'] = types.SimpleNamespace(connect=fake_connect)

from services.etl import helium_fees_ingestor


def test_offline(monkeypatch):
    os.environ['ENABLE_LIVE'] = '0'
    os.environ['HELIUM_API_KEY'] = 'k'
    os.environ['PG_DSN'] = 'dsn'
    res = helium_fees_ingestor.main()
    assert res == 0

