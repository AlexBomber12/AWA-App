from __future__ import annotations

import pytest

from services.logistics_etl import flow


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


def _install_success(monkeypatch: pytest.MonkeyPatch, stub_load_log):
    session = _StubSession()
    engine = _StubEngine()
    snapshot = {"source": "s3://example/rates.csv", "raw": b"123", "meta": {"seqno": "1"}, "rows": [1, 2]}

    async def fake_collect_inputs():
        return [snapshot], []

    async def fake_process(snapshots, **kwargs):
        return [
            {
                "source": snapshots[0]["source"],
                "rows_upserted": 2,
                "rows_in": len(snapshots[0].get("rows") or []),
                "skipped": False,
                "status": "success",
            }
        ]

    monkeypatch.setattr(flow, "_collect_inputs", fake_collect_inputs)
    monkeypatch.setattr(flow, "_process_snapshots", fake_process)
    monkeypatch.setattr(flow, "create_engine", lambda *a, **k: engine)
    monkeypatch.setattr(flow, "sessionmaker", lambda *a, **k: (lambda: session))
    return engine


def test_logistics_run_skips_duplicate(monkeypatch: pytest.MonkeyPatch, stub_load_log) -> None:
    engine = _install_success(monkeypatch, stub_load_log)

    flow.run_once_with_guard(dry_run=False)
    statuses_first = {record["status"] for record in stub_load_log.values()}
    assert "success" in statuses_first

    flow.run_once_with_guard(dry_run=False)
    statuses_second = {record["status"] for record in stub_load_log.values()}
    assert "skipped" in statuses_second
    assert engine.disposed


def test_logistics_run_failure(monkeypatch: pytest.MonkeyPatch, stub_load_log) -> None:
    session = _StubSession()
    engine = _StubEngine()

    async def fake_collect_inputs():
        return ([{"source": "s3://example.csv", "raw": b"", "meta": {}, "rows": []}], [])

    async def boom(_snapshots, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(flow, "_collect_inputs", fake_collect_inputs)
    monkeypatch.setattr(flow, "_process_snapshots", boom)
    monkeypatch.setattr(flow, "create_engine", lambda *a, **k: engine)
    monkeypatch.setattr(flow, "sessionmaker", lambda *a, **k: (lambda: session))

    with pytest.raises(RuntimeError):
        flow.run_once_with_guard(dry_run=False)
    statuses = {record["status"] for record in stub_load_log.values()}
    assert "failed" in statuses
    assert engine.disposed
