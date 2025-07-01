import os
import types
import sys

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

from services.etl import sp_fees_ingestor


def test_offline(monkeypatch, tmp_path):
    os.environ['ENABLE_LIVE'] = '0'
    os.environ['SP_REFRESH_TOKEN'] = 't'
    os.environ['SP_CLIENT_ID'] = 'i'
    os.environ['SP_CLIENT_SECRET'] = 's'
    os.environ['SELLER_ID'] = 'seller'
    os.environ['REGION'] = 'EU'
    os.environ['PG_DSN'] = 'dsn'
    res = sp_fees_ingestor.main()
    assert res == 0
