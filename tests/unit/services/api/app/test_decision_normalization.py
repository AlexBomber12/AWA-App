from __future__ import annotations

import datetime as dt
from types import SimpleNamespace

import pytest

from services.api.app.decision import repository, service
from services.api.app.decision.models import (
    DecisionTaskRecord,
    PlannedDecisionTask,
    normalize_alternatives,
    normalize_links,
    normalize_reasons,
)
from services.api.routes import decision_serializers


def test_normalize_reasons_and_alternatives_cover_branches():
    reasons = normalize_reasons([None, "text", {"code": "c1", "detail": "d1", "metric": "1.5"}])
    assert reasons[0] == {"code": "info", "message": "text"}
    assert any(reason["data"]["detail"] == "d1" for reason in reasons if "data" in reason)

    alts = normalize_alternatives(
        [
            "wait",
            {
                "decision": "switch",
                "impact": "high",
                "confidence": "0.8",
                "why": [{"code": "nested", "message": "because"}],
            },
        ]
    )
    assert alts[0]["action"] == "wait"
    assert alts[1]["impact"] == "high"
    assert alts[1]["why"][0]["code"] == "nested"


def test_normalize_links_allows_known_keys():
    data = {
        "asin": "A1",
        "vendor_id": 1,
        "links": {"campaign_id": 9, "unknown": "x"},
        "entity": {"price_list_row_id": "row-1", "entity_id": "ent-1"},
    }
    links = normalize_links(data)
    assert links["asin"] == "A1"
    assert links["vendor_id"] == 1
    assert links["campaign_id"] == 9
    assert links["price_list_row_id"] == "row-1"
    assert "unknown" not in links


def test_sort_clause_created_at_branch():
    clause = repository._sort_clause("created_at")
    assert len(clause) == 2
    assert clause[0].element.name == "created_at"


def test_links_for_plan_merges_entity_fields():
    plan = PlannedDecisionTask(
        asin="B1",
        vendor_id=10,
        decision="continue",
        priority=5,
        summary="s",
        default_action=None,
        why=[],
        alternatives=[],
        entity={"campaign_id": 7},
    )
    links = repository._links_for_plan(plan)
    assert links["asin"] == "B1"
    assert links["vendor_id"] == 10
    assert links["campaign_id"] == 7


@pytest.mark.asyncio
async def test_apply_and_dismiss_log_and_metrics(monkeypatch):
    record = DecisionTaskRecord(
        id="t1",
        source="src",
        entity={},
        decision="request_price",
        priority=50,
        state="pending",
        summary=None,
        entity_type="sku_vendor",
        asin="A1",
        vendor_id=1,
        thread_id=None,
        deadline_at=None,
        default_action=None,
        why=[],
        alternatives=[],
        metrics=None,
        next_request_at=None,
        assignee=None,
        created_at=None,
        updated_at=None,
        links={"asin": "A1"},
    )

    async def _update_task_state(session, task_id, new_state, **kwargs):
        return record

    async def _summarize_states(session, conditions):
        return {"pending": 1}

    monkeypatch.setattr(repository, "update_task_state", _update_task_state)
    monkeypatch.setattr(repository, "summarize_states", _summarize_states)

    session = SimpleNamespace()
    applied = await service.apply_task(session, "t1", actor="user", note="ok")
    dismissed = await service.dismiss_task(session, "t1", actor="user", note="skip")
    assert applied is record and dismissed is record


def test_serializer_typed_alternatives_and_links():
    record = DecisionTaskRecord(
        id="t-typed",
        source="decision_engine",
        entity={"asin": "A1", "vendor_id": 2},
        decision="continue",
        priority=20,
        state="pending",
        summary="sum",
        entity_type="sku_vendor",
        asin="A1",
        vendor_id=2,
        thread_id="thread-1",
        deadline_at=dt.datetime.now(dt.UTC),
        default_action="act",
        why=[{"code": "c1", "message": "m1"}],
        alternatives=[{"action": "wait", "impact": "low", "why": [{"code": "r1", "message": "nested"}]}],
        metrics={"roi": 12},
        next_request_at=None,
        assignee="ops",
        created_at=dt.datetime.now(dt.UTC),
        updated_at=dt.datetime.now(dt.UTC),
        links={"asin": "A1", "vendor_id": 2, "thread_id": "thread-1"},
    )
    serialized = decision_serializers.serialize_task(record)
    assert serialized.links.asin == "A1"
    assert serialized.alternatives[0].why[0].code == "r1"
