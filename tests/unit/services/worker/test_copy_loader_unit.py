import types

import pandas as pd

from services.worker import copy_loader


class SQLStub:
    def __init__(self, text):
        self.text = text

    def format(self, *args):
        formatted = self.text
        for arg in args:
            value = getattr(arg, "text", str(arg))
            formatted = formatted.replace("{}", value, 1)
        return SQLStub(formatted)

    def join(self, seq):
        values = [getattr(item, "text", str(item)) for item in seq]
        return SQLStub(self.text.join(values))

    def as_string(self, _conn):
        return self.text

    def __str__(self):
        return self.text


def _patch_sql(monkeypatch):
    module = types.SimpleNamespace(
        SQL=lambda text: SQLStub(text), Identifier=lambda name: SQLStub(f'"{name}"')
    )
    monkeypatch.setattr(copy_loader, "sql", module)


class DummyCursor:
    def __init__(self, log):
        self.log = log

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, stmt):
        self.log.append(str(stmt))

    def copy_expert(self, stmt, buf):
        self.log.append(("copy", stmt, buf.read()))


class DummyConnection:
    def __init__(self):
        self.log = []
        self.autocommit = False
        self.closed = False
        self.committed = False

    def cursor(self):
        return DummyCursor(self.log)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.log.append("rollback")

    def close(self):
        self.closed = True


class DummyEngine:
    def __init__(self, conn):
        self._conn = conn

    def raw_connection(self):
        return self._conn


def test_copy_loader_inserts_rows(monkeypatch):
    _patch_sql(monkeypatch)
    conn = DummyConnection()
    engine = DummyEngine(conn)
    df = pd.DataFrame([[1, 2]], columns=["id", "value"])
    inserted = copy_loader.copy_df_via_temp(
        engine, df, target_table="items", columns=["id", "value"], conflict_cols=["id"]
    )
    assert inserted == 1
    assert conn.committed is True
    assert any("ON CONFLICT" in stmt for stmt in conn.log if isinstance(stmt, str))


def test_copy_loader_returns_zero_for_empty(monkeypatch):
    _patch_sql(monkeypatch)
    engine = DummyEngine(DummyConnection())
    df = pd.DataFrame(columns=["id"])
    assert copy_loader.copy_df_via_temp(engine, df, "tbl", columns=["id"]) == 0
