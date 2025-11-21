import pytest

from services.api.app.decision import repository
from tests.unit.conftest import _StubResult


@pytest.mark.asyncio
async def test_update_task_state_inserts_event(fake_db_session):
    current = {"id": "task-1", "state": "pending", "decision": "request_price"}
    updated = {"id": "task-1", "state": "applied", "decision": "request_price"}
    session = fake_db_session(_StubResult(mappings=[current]), _StubResult(mappings=[updated]))

    result = await repository.update_task_state(session, "task-1", "applied", actor="ops@example.com", note="done")
    assert result is not None
    assert result.state == "applied"
    assert session.committed is True
    assert len(session.executed) == 3
    insert_stmt, _params = session.executed[-1]
    assert "events" in str(insert_stmt).lower()


@pytest.mark.asyncio
async def test_list_tasks_returns_items_and_summary(fake_db_session):
    task_row = {
        "id": "t-1",
        "source": "decision_engine",
        "entity": {},
        "decision": "request_discount",
        "priority": 60,
        "state": "pending",
    }
    session = fake_db_session(
        _StubResult(mappings=[task_row]),
        _StubResult(scalar=1),
        _StubResult(mappings=[("pending", 1)]),
    )

    items, total, summary = await repository.list_tasks(session, page=1, page_size=10)
    assert total == 1
    assert len(items) == 1
    assert items[0].decision == "request_discount"
    assert summary["pending"] == 1
