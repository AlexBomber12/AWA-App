import pytest

from services.api.app.decision import service
from services.api.app.decision.models import DecisionCandidate


def test_observe_only_candidate_generates_blocked_task():
    candidate = DecisionCandidate(asin="A1", vendor_id=1, cost=10.0, roi_pct=15.0, observe_only=True)
    plan = service._evaluate_candidate(candidate)  # type: ignore[attr-defined]  # noqa: SLF001
    assert plan is not None
    assert plan.decision == "blocked_observe"
    assert plan.priority == service.OBSERVE_PRIORITY


def test_critical_roi_requests_price_update():
    candidate = DecisionCandidate(asin="A2", vendor_id=7, cost=12.0, roi_pct=-10.0)
    plan = service._evaluate_candidate(candidate)  # type: ignore[attr-defined]  # noqa: SLF001
    assert plan is not None
    assert plan.decision == "request_price"
    assert any(isinstance(reason, dict) and reason.get("code") == "roi_guardrail" for reason in plan.why)


def test_high_roi_skips_decision():
    candidate = DecisionCandidate(asin="A3", vendor_id=None, cost=9.0, roi_pct=25.0)
    plan = service._evaluate_candidate(candidate)  # type: ignore[attr-defined]  # noqa: SLF001
    assert plan is None


@pytest.mark.asyncio
async def test_generate_tasks_dry_run(monkeypatch, fake_db_session):
    candidates = [
        DecisionCandidate(asin="B1", vendor_id=3, cost=10.0, roi_pct=-2.0),
        DecisionCandidate(asin="B2", vendor_id=None, cost=7.0, roi_pct=-8.0),
    ]

    async def _fake_fetch(_session, limit=0):  # noqa: ANN001
        assert limit == 5
        return candidates

    monkeypatch.setattr(service.repository, "fetch_decision_candidates", _fake_fetch)
    session = fake_db_session()
    saved, plans, candidates_count = await service.generate_tasks(session, limit=5, dry_run=True)
    assert saved == []
    assert candidates_count == len(candidates)
    assert any(plan.decision == "request_discount" for plan in plans)
