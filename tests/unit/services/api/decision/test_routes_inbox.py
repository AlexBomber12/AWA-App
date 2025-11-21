from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import services.api.main as api_main
import services.api.security as security
from awa_common.db.async_session import get_async_session
from awa_common.security.models import Role, UserCtx
from services.api.app.decision import repository as decision_repository, service as decision_service
from services.api.app.decision.models import DecisionTaskRecord


@pytest.fixture
def ops_user(dummy_user_ctx) -> UserCtx:
    return dummy_user_ctx(roles=[Role.ops])


@pytest.fixture
def inbox_client(fastapi_dep_overrides, ops_user):
    app = api_main.app

    async def _ops():
        return ops_user

    def _limit_provider():
        async def _noop(_request):
            return None

        return _noop

    original = dict(app.dependency_overrides)

    async def _fake_session():
        yield object()

    app.dependency_overrides.update(
        {
            security.require_ops: _ops,
            security.limit_ops: _limit_provider,
            get_async_session: _fake_session,
        }
    )
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original)


def _task_record(task_id: str = "t-1") -> DecisionTaskRecord:
    return DecisionTaskRecord.from_mapping(
        {
            "id": task_id,
            "source": "decision_engine",
            "entity": {"asin": "X1"},
            "decision": "request_price",
            "priority": 90,
            "state": "pending",
            "why": [],
            "alternatives": [],
        }
    )


def test_inbox_list(monkeypatch, inbox_client):
    async def _fake_list(*_args, **_kwargs):
        return [_task_record()], 1, {"pending": 1}

    monkeypatch.setattr(decision_repository, "list_tasks", _fake_list)
    response = inbox_client.get("/inbox/tasks")
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 1
    assert body["items"][0]["decision"] == "request_price"


def test_inbox_apply(monkeypatch, inbox_client):
    task = _task_record()

    async def _fake_apply(*_args, **_kwargs):
        return task

    monkeypatch.setattr(decision_service, "apply_task", _fake_apply)
    response = inbox_client.post("/inbox/tasks/t-1/apply", json={"note": "done"})
    assert response.status_code == 200
    assert response.json()["id"] == "t-1"


def test_inbox_dismiss(monkeypatch, inbox_client):
    task = _task_record("t-2")

    async def _fake_dismiss(*_args, **_kwargs):
        return task

    monkeypatch.setattr(decision_service, "dismiss_task", _fake_dismiss)
    response = inbox_client.post("/inbox/tasks/t-2/dismiss", json={"note": "skip"})
    assert response.status_code == 200
    assert response.json()["id"] == "t-2"
