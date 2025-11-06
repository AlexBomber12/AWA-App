from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from awa_common.db.load_log import (
    mark_failed,
    mark_success,
    soft_update_meta_on_duplicate,
    try_insert_load_log,
)
from sqlalchemy import insert


@dataclass
class DummyResult:
    value: Any

    def scalar_one_or_none(self) -> Any:
        return self.value


class StubSession:
    def __init__(self, results: list[DummyResult] | None = None) -> None:
        self._results = results or []
        self.executed: list[tuple[Any, Any | None]] = []
        self.flushed = False
        self.committed = False

    def execute(self, statement: Any, params: Any | None = None) -> DummyResult | None:
        self.executed.append((statement, params))
        if self._results:
            return self._results.pop(0)
        return None

    def flush(self) -> None:
        self.flushed = True

    def commit(self) -> None:
        self.committed = True


def _unwrap_insert(stmt: Any) -> Any:
    # SQLAlchemy may wrap statements in Cached objects in tests; unwrap when needed.
    if hasattr(stmt, "element"):
        return stmt.element
    return stmt


def test_try_insert_load_log_inserts_and_flushes() -> None:
    session = StubSession(results=[DummyResult(42)])
    status = try_insert_load_log(
        session,
        source="etl",
        idempotency_key="abc",
        payload_meta={"mode": "test"},
        processed_by="worker",
        task_id="task-1",
    )
    assert status == "inserted"
    assert session.flushed
    stmt, params = session.executed[0]
    stmt = _unwrap_insert(stmt)
    assert isinstance(stmt, insert)
    compiled = str(stmt)
    assert "load_log" in compiled
    assert params is None  # SQLAlchemy uses bound parameters inside statement


def test_try_insert_returns_duplicate_without_flush() -> None:
    session = StubSession(results=[DummyResult(None)])
    status = try_insert_load_log(
        session,
        source="etl",
        idempotency_key="dup",
        payload_meta={},
        processed_by=None,
        task_id=None,
    )
    assert status == "duplicate"
    assert not session.flushed


def test_mark_success_updates_duration() -> None:
    session = StubSession()
    mark_success(session, load_log_id=10, duration_ms=1234)
    stmt, params = session.executed[0]
    assert "UPDATE load_log" in str(stmt)
    assert params is None


def test_mark_failed_persists_error_message() -> None:
    session = StubSession()
    mark_failed(session, load_log_id=5, error_message="boom")
    stmt, params = session.executed[0]
    assert "status" in str(stmt)


def test_soft_update_meta_on_duplicate_updates_fields() -> None:
    session = StubSession()
    soft_update_meta_on_duplicate(
        session,
        source="etl",
        idempotency_key="dup",
        payload_meta={"foo": "bar"},
        processed_by="worker",
        task_id="task-2",
    )
    stmt, params = session.executed[0]
    assert "UPDATE load_log" in str(stmt)
