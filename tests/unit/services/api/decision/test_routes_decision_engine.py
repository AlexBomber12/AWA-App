from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import services.api.main as api_main
import services.api.security as security
from awa_common.db.async_session import get_async_session
from awa_common.security.models import Role, UserCtx
from services.api.app.decision import repository as decision_repository, service as decision_service
from services.api.app.decision.models import DecisionTaskRecord, PlannedDecisionTask


@pytest.fixture
def admin_user(dummy_user_ctx) -> UserCtx:
    return dummy_user_ctx(roles=[Role.admin])


@pytest.fixture
def client_with_overrides(fastapi_dep_overrides, admin_user):
    app = api_main.app

    async def _admin():
        return admin_user

    def _limit_provider():
        async def _noop(_request):
            return None

        return _noop

    original = dict(app.dependency_overrides)

    async def _fake_session():
        yield object()

    app.dependency_overrides.update(
        {
            security.require_admin: _admin,
            security.require_ops: _admin,
            security.limit_ops: _limit_provider,
            get_async_session: _fake_session,
        }
    )
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original)


def test_decision_preview_route(monkeypatch, client_with_overrides):
    planned = PlannedDecisionTask(
        asin="B1",
        vendor_id=1,
        decision="request_price",
        priority=90,
        summary="need price",
        default_action=None,
        why=[],
        alternatives=[],
    )
    planned.entity = {"type": "sku_vendor", "asin": "B1", "vendor_id": 1}

    async def _fake_generate(*_args, **_kwargs):
        return [], [planned], 1

    monkeypatch.setattr(decision_service, "generate_tasks", _fake_generate)
    response = client_with_overrides.get("/decision/preview")
    assert response.status_code == 200
    body = response.json()
    assert body["generated"] == 1
    assert body["planned"][0]["decision"] == "request_price"


def test_decision_run_route(monkeypatch, client_with_overrides):
    task = DecisionTaskRecord.from_mapping(
        {
            "id": "t-100",
            "source": "decision_engine",
            "entity": {"asin": "C1"},
            "decision": "continue",
            "priority": 10,
            "state": "pending",
            "why": [],
            "alternatives": [],
        }
    )

    async def _fake_generate(*_args, **_kwargs):
        return [task], [], 1

    async def _fake_summary(*_args, **_kwargs):
        return {"pending": 1}

    monkeypatch.setattr(decision_service, "generate_tasks", _fake_generate)
    monkeypatch.setattr(decision_repository, "summarize_states", _fake_summary)
    response = client_with_overrides.post("/decision/run")
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["decision"] == "continue"
    assert data["summary"]["pending"] == 1
