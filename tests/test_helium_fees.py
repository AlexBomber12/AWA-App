import os
import sys
import types
import requests


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


connections = []

def fake_connect(dsn):
    conn = FakeConn()
    connections.append(conn)
    return conn


calls = []

def fake_get(url):
    calls.append(url)
    return types.SimpleNamespace(json=lambda: {"fee": 0}, raise_for_status=lambda: None)


def test_offline(monkeypatch):
    monkeypatch.setattr(requests, 'get', fake_get)
    monkeypatch.setitem(sys.modules, 'psycopg2', types.SimpleNamespace(connect=fake_connect))
    os.environ.pop('ENABLE_LIVE', None)
    os.environ['PG_DSN'] = 'dsn'
    from services.etl import helium_fees
    res = helium_fees.main()
    inserts = [s for s in connections[0].c.stmts if s[0].startswith('INSERT INTO fees_raw')]
    assert res == 0
    assert calls == []
    assert [p for q, p in inserts] == [('DUMMY1', 1.11), ('DUMMY2', 2.22)]
