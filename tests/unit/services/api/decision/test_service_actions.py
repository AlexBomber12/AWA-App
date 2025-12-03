from __future__ import annotations

import datetime as dt

import pytest

from services.api.app.decision import repository, service
from services.api.app.decision.models import DecisionTaskRecord


def _task_record(task_id: str, decision: str = "request_price", state: str = "pending") -> DecisionTaskRecord:
    return DecisionTaskRecord.from_mapping(
        {
            "id": task_id,
            "source": "decision_engine",
            "entity": {"asin": "X1"},
            "decision": decision,
            "priority": 80,
            "state": state,
            "why": [],
            "alternatives": [],
        }
    )


@pytest.mark.asyncio
async def test_snooze_task_updates_state_and_gauge(monkeypatch, fake_db_session):
    called = {"gauge": False, "state": None}

    async def _fake_update(session, task_id, new_state, **kwargs):
        called["state"] = new_state
        assert kwargs.get("next_request_at") is not None
        return _task_record(task_id, state=new_state)

    async def _fake_gauge(session):
        called["gauge"] = True

    monkeypatch.setattr(repository, "update_task_state", _fake_update)
    monkeypatch.setattr(service, "_update_inbox_gauge", _fake_gauge)

    result = await service.snooze_task(
        fake_db_session,
        "task-snooze",
        actor="ops@example.com",
        note="later",
        next_request_at=dt.datetime.now(dt.UTC),
    )

    assert result is not None
    assert called["state"] == "snoozed"
    assert called["gauge"] is True


@pytest.mark.asyncio
async def test_reopen_task_updates_state_and_gauge(monkeypatch, fake_db_session):
    called = {"gauge": False, "state": None}

    async def _fake_update(session, task_id, new_state, **kwargs):
        called["state"] = new_state
        return _task_record(task_id, state=new_state)

    async def _fake_gauge(session):
        called["gauge"] = True

    monkeypatch.setattr(repository, "update_task_state", _fake_update)
    monkeypatch.setattr(service, "_update_inbox_gauge", _fake_gauge)

    result = await service.reopen_task(fake_db_session, "task-reopen", actor="ops@example.com", note="undo")

    assert result is not None
    assert called["state"] == "pending"
    assert called["gauge"] is True
