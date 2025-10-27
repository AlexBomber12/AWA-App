from types import SimpleNamespace

import awa_common.keepa as keepa


def test_list_active_asins(monkeypatch):
    rows = [("A1",), ("B2",)]

    class DummyConn:
        def execute(self, stmt):
            return SimpleNamespace(fetchall=lambda: rows)

    class DummyEngine:
        def begin(self):
            return self

        def __enter__(self):
            return DummyConn()

        def __exit__(self, exc_type, exc, tb):
            return False

        def dispose(self):
            return None

    monkeypatch.setattr(keepa, "create_engine", lambda _dsn: DummyEngine())
    result = keepa.list_active_asins()
    assert result == ["A1", "B2"]
