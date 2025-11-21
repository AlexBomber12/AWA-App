import datetime as dt

import pytest

from services.api.app.decision import repository
from services.api.app.decision.models import PlannedDecisionTask
from services.api.roi_views import InvalidROIViewError
from tests.unit.conftest import _StubResult


@pytest.mark.asyncio
async def test_fetch_decision_candidates_uses_limit(monkeypatch, fake_db_session):
    captured = {}

    async def _fake_execute(stmt, params):
        captured["sql"] = str(stmt)
        captured["params"] = params
        return _StubResult(
            mappings=[{"asin": "A1", "vendor_id": 1, "cost": 10, "roi_pct": 5, "buybox_price": 12, "fees": 1}]
        )

    session = fake_db_session()
    session.execute = _fake_execute  # type: ignore[assignment]
    monkeypatch.setattr(repository, "get_roi_view_name", lambda: "v_roi_full")
    candidates = await repository.fetch_decision_candidates(session, limit=3)
    assert captured["params"]["limit"] == 3
    assert candidates[0].asin == "A1"


@pytest.mark.asyncio
async def test_list_tasks_with_search_and_summary(fake_db_session):
    tasks_row = {
        "id": "t-1",
        "source": "decision_engine",
        "entity": {},
        "decision": "request_discount",
        "priority": 60,
        "state": "pending",
        "total_count": 1,
    }
    session = fake_db_session(
        _StubResult(mappings=[tasks_row]),
        _StubResult(scalar=1),
        _StubResult(mappings=[("pending", 1)]),
    )
    items, total, summary = await repository.list_tasks(
        session,
        page=1,
        page_size=10,
        state="pending",
        source="decision_engine",
        priority=50,
        assignee=None,
        search="discount",
        task_id=None,
        sort="deadline",
    )
    assert total == 1
    assert items[0].decision == "request_discount"
    assert summary["pending"] == 1


@pytest.mark.asyncio
async def test_upsert_tasks_updates_existing(fake_db_session):
    existing_row = {"id": "t-1", "asin": "A1", "vendor_id": 5, "decision": "request_price", "state": "pending"}
    updated_row = {
        "id": "t-1",
        "asin": "A1",
        "vendor_id": 5,
        "decision": "request_price",
        "state": "pending",
        "summary": "updated",
    }
    session = fake_db_session(
        _StubResult(mappings=[existing_row]),
        _StubResult(mappings=[updated_row]),
    )
    plan = PlannedDecisionTask(
        asin="A1",
        vendor_id=5,
        decision="request_price",
        priority=90,
        summary="new",
        default_action=None,
        why=[],
        alternatives=[],
        deadline_at=dt.datetime.now(dt.UTC),
    )
    plan.entity = {"asin": "A1", "vendor_id": 5}
    saved = await repository.upsert_tasks(session, [plan], now=dt.datetime.now(dt.UTC))
    assert saved[0].summary == "updated"


@pytest.mark.asyncio
async def test_upsert_tasks_inserts_when_missing(fake_db_session):
    inserted_row = {"id": "t-2", "asin": "B1", "vendor_id": None, "decision": "continue", "state": "pending"}
    session = fake_db_session(_StubResult(mappings=[]), _StubResult(mappings=[inserted_row]))
    plan = PlannedDecisionTask(
        asin="B1",
        vendor_id=None,
        decision="continue",
        priority=20,
        summary="ok",
        default_action=None,
        why=[],
        alternatives=[],
    )
    saved = await repository.upsert_tasks(session, [plan], now=dt.datetime.now(dt.UTC))
    assert saved[0].id == "t-2"


@pytest.mark.asyncio
async def test_fetch_decision_candidates_handles_invalid_view(monkeypatch, fake_db_session):
    monkeypatch.setattr(repository, "get_roi_view_name", lambda: "")
    session = fake_db_session()
    with pytest.raises(InvalidROIViewError):
        await repository.fetch_decision_candidates(session)
