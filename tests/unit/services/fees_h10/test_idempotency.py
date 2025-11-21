from __future__ import annotations

import pytest

from services.fees_h10 import worker


class _StubSession:
    def __init__(self) -> None:
        self.executed: list[tuple] = []
        self.closed = False

    def execute(self, stmt, params=None):
        self.executed.append((stmt, params))

    def commit(self):
        return None

    def rollback(self):
        return None

    def close(self):
        self.closed = True


class _StubEngine:
    def __init__(self) -> None:
        self.disposed = False

    def dispose(self):
        self.disposed = True


def _install_stubs(monkeypatch: pytest.MonkeyPatch, stub_load_log, run_result) -> _StubEngine:
    session = _StubSession()
    engine = _StubEngine()
    monkeypatch.setattr(worker, "create_engine", lambda *a, **k: engine)
    monkeypatch.setattr(worker, "sessionmaker", lambda *a, **k: (lambda: session))
    monkeypatch.setattr(worker, "list_active_asins", lambda: ["A1"])

    async def fake_run_refresh(asins):
        if isinstance(run_result, Exception):
            raise run_result
        return run_result

    monkeypatch.setattr(worker, "_run_refresh", fake_run_refresh)
    return engine


def test_refresh_fees_idempotent_skip(monkeypatch: pytest.MonkeyPatch, stub_load_log) -> None:
    engine = _install_stubs(
        monkeypatch,
        stub_load_log,
        {"requested": 1, "processed": 1, "inserted": 1, "updated": 0, "failures": 0},
    )
    worker.refresh_fees()
    statuses_after_first = {record["status"] for record in stub_load_log.values()}
    assert "success" in statuses_after_first

    worker.refresh_fees()

    statuses = {record["status"] for record in stub_load_log.values()}
    assert "skipped" in statuses
    assert engine.disposed


def test_refresh_fees_failure_marks_failed(monkeypatch: pytest.MonkeyPatch, stub_load_log) -> None:
    engine = _install_stubs(monkeypatch, stub_load_log, RuntimeError("boom"))
    with pytest.raises(RuntimeError):
        worker.refresh_fees()
    statuses = {record["status"] for record in stub_load_log.values()}
    assert "failed" in statuses
    assert engine.disposed
