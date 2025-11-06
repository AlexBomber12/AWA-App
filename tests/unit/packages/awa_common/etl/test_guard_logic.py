from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any

import pytest

from awa_common.etl import guard


class StubSession(AbstractContextManager):
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closed = True
        return None

    def __exit__(self, *exc_info: Any) -> None:  # pragma: no cover - not used
        self.close()


@pytest.fixture
def session_factory(monkeypatch: pytest.MonkeyPatch):
    created: list[StubSession] = []

    def factory() -> StubSession:
        session = StubSession()
        created.append(session)
        return session

    monkeypatch.setattr(guard, "try_insert_load_log", lambda *a, **k: "inserted")
    monkeypatch.setattr(guard, "get_load_log_id", lambda *a, **k: 1)
    monkeypatch.setattr(guard, "mark_success", lambda *a, **k: None)
    monkeypatch.setattr(guard, "mark_failed", lambda *a, **k: None)
    monkeypatch.setattr(guard, "soft_update_meta_on_duplicate", lambda *a, **k: None)
    return {"factory": factory, "created": created}


def test_process_once_success_flow(session_factory):
    with guard.process_once(
        session_factory["factory"],
        source="demo",
        payload_meta={"mode": "test"},
        idempotency_key="abc",
    ) as handle:
        assert handle is not None
    sessions = session_factory["created"]
    assert sessions and sessions[0].closed


def test_process_once_duplicate_skip(monkeypatch, session_factory):
    monkeypatch.setattr(guard, "try_insert_load_log", lambda *a, **k: "duplicate")
    with guard.process_once(
        session_factory["factory"],
        source="demo",
        payload_meta={},
        idempotency_key="dup",
    ) as handle:
        assert handle is None


def test_process_once_duplicate_update(monkeypatch, session_factory):
    updates: list[tuple[str, Any]] = []

    def update_meta(*_args, **kwargs):
        updates.append(("update", kwargs))

    monkeypatch.setattr(guard, "try_insert_load_log", lambda *a, **k: "duplicate")
    monkeypatch.setattr(guard, "soft_update_meta_on_duplicate", update_meta)
    with guard.process_once(
        session_factory["factory"],
        source="demo",
        payload_meta={"refresh": True},
        idempotency_key="dup",
        on_duplicate="update_meta",
    ) as handle:
        assert handle is None
    assert updates and updates[0][1]["payload_meta"] == {"refresh": True}


def test_process_once_failure_marks_failed(monkeypatch, session_factory):
    flags: dict[str, bool] = {"failed": False}

    def fail_marker(*_args, **_kwargs):
        flags["failed"] = True

    monkeypatch.setattr(guard, "mark_failed", fail_marker)

    with pytest.raises(RuntimeError):
        with guard.process_once(
            session_factory["factory"],
            source="demo",
            payload_meta={},
            idempotency_key="oops",
        ):
            raise RuntimeError("boom")
    assert flags["failed"]
