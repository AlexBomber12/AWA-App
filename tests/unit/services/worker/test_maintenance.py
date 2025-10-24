from services.worker import maintenance as maintenance_module


class DummyConn:
    def __init__(self, log):
        self.log = log

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, stmt, params=None):
        self.log.append((str(stmt), params))


class DummyEngine:
    def __init__(self):
        self.log = []

    def begin(self):
        return DummyContext(self.log)

    def dispose(self):
        self.log.append("dispose")


class DummyContext:
    def __init__(self, log):
        self.log = log

    def __enter__(self):
        return DummyConn(self.log)

    def __exit__(self, exc_type, exc, tb):
        return False


def test_task_analyze_table(monkeypatch):
    engine = DummyEngine()
    monkeypatch.setattr(maintenance_module, "create_engine", lambda *_: engine)
    result = maintenance_module.task_analyze_table("public.table")
    assert result["status"] == "success"
    assert any("ANALYZE" in stmt for stmt, _ in engine.log)


def test_task_maintenance_nightly(monkeypatch):
    engine = DummyEngine()
    monkeypatch.setenv("TABLE_MAINTENANCE_LIST", "public.a, public.b")
    monkeypatch.setenv("VACUUM_ENABLE", "true")
    monkeypatch.setattr(maintenance_module, "create_engine", lambda *_: engine)
    result = maintenance_module.task_maintenance_nightly()
    assert result["status"] == "success"
    assert len(result["tables"]) == 2
    assert any("VACUUM" in stmt for stmt, _ in engine.log)
