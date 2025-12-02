from __future__ import annotations

import datetime as dt

from services.api.app.decision import service
from services.api.app.decision.models import DecisionCandidate


def test_evaluate_candidate_builds_canonical_reason(monkeypatch):
    fixed_now = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
    monkeypatch.setattr(service, "_now", lambda: fixed_now)
    candidate = DecisionCandidate(
        asin="A1",
        vendor_id=1,
        cost=10.0,
        roi_pct=-12.5,
        category="beauty",
    )
    plan = service._evaluate_candidate(candidate)
    assert plan is not None
    assert plan.decision == "request_price"
    assert plan.priority == service.REQUEST_PRIORITY
    assert plan.deadline_at == fixed_now + dt.timedelta(days=2)
    assert plan.links["asin"] == "A1"
    assert plan.links["vendor_id"] == 1
    reason = plan.why[0]
    assert reason["code"] == "roi_guardrail"
    assert "message" in reason
    alternative = plan.alternatives[0]
    assert alternative["action"] == "wait_until"


def test_evaluate_candidate_skips_missing_roi(monkeypatch):
    monkeypatch.setattr(service, "_now", lambda: dt.datetime(2024, 1, 1, tzinfo=dt.UTC))
    candidate = DecisionCandidate(asin="A2", vendor_id=None, cost=None, roi_pct=None)
    assert service._evaluate_candidate(candidate) is None


def test_evaluate_candidate_continue_path(monkeypatch):
    fixed_now = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
    monkeypatch.setattr(service, "_now", lambda: fixed_now)
    candidate = DecisionCandidate(asin="A3", vendor_id=10, cost=8.4, roi_pct=14.0)
    plan = service._evaluate_candidate(candidate)
    assert plan is not None
    assert plan.decision == "continue"
    assert plan.deadline_at is None
    assert any(reason["code"] == "roi_ok" for reason in plan.why)
