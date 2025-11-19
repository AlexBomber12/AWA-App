import pytest

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


class RefreshExecutionContext:
    def __init__(self, connection, log):
        self.connection = connection
        self.log = log

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


class RefreshConnection:
    def __init__(self, log, raise_on_first=False):
        self.log = log
        self.raise_on_first = raise_on_first
        self.calls = 0

    def execution_options(self, **options):
        self.log.append(("execution_options", options))
        return RefreshExecutionContext(self, self.log)

    def execute(self, stmt, params=None):
        self.calls += 1
        self.log.append(str(stmt))
        if self.raise_on_first and self.calls == 1:
            raise RuntimeError("refresh failed")


class RefreshEngine:
    def __init__(self, raise_on_first=False):
        self.log = []
        self.raise_on_first = raise_on_first
        self.disposed = False

    def connect(self):
        return RefreshConnection(self.log, self.raise_on_first)

    def dispose(self):
        self.disposed = True


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


def test_task_refresh_roi_mvs_executes_both_views(monkeypatch):
    engine = RefreshEngine()
    monkeypatch.setattr(maintenance_module, "create_engine", lambda *_: engine)
    monkeypatch.setattr(
        maintenance_module,
        "_bust_stats_cache",
        lambda *_: {"status": "success", "deleted": {"kpi": 1, "roi_trend": 0, "returns": 0}},
    )
    monkeypatch.setattr(maintenance_module.settings, "ROI_MATERIALIZED_VIEW_NAME", "custom_roi_mat", raising=False)
    result = maintenance_module.task_refresh_roi_mvs.run()
    assert result == {
        "status": "success",
        "views": ["custom_roi_mat", "mat_fees_expanded"],
        "cache_bust": {"status": "success", "deleted": {"kpi": 1, "roi_trend": 0, "returns": 0}},
    }
    assert engine.disposed is True
    assert engine.log[0] == ("execution_options", {"isolation_level": "AUTOCOMMIT"})
    assert engine.log[1] == 'REFRESH MATERIALIZED VIEW CONCURRENTLY "custom_roi_mat"'
    assert engine.log[2] == "REFRESH MATERIALIZED VIEW CONCURRENTLY mat_fees_expanded"


def test_task_refresh_roi_mvs_raises_and_disposes(monkeypatch):
    engine = RefreshEngine(raise_on_first=True)
    monkeypatch.setattr(maintenance_module, "create_engine", lambda *_: engine)
    monkeypatch.setattr(maintenance_module.settings, "ROI_MATERIALIZED_VIEW_NAME", "custom_roi_mat", raising=False)
    with pytest.raises(RuntimeError):
        maintenance_module.task_refresh_roi_mvs.run()
    assert engine.disposed is True
    assert engine.log[0] == ("execution_options", {"isolation_level": "AUTOCOMMIT"})
    assert engine.log[1] == 'REFRESH MATERIALIZED VIEW CONCURRENTLY "custom_roi_mat"'
    assert len(engine.log) == 2
