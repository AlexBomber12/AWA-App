import datetime as dt

import pytest

from services.api.app.decision import service
from services.api.app.decision.models import DecisionCandidate


class _StubMetric:
    def __init__(self):
        self.calls: list[dict[str, str]] = []

    def labels(self, **labels):
        self.calls.append(labels)
        return self

    def observe(self, _value):
        return None

    def inc(self, _value=1):
        return None

    def set(self, _value):
        return None


def test_metric_labels_returns_dict():
    labels = service._metric_labels(decision="test")  # type: ignore[attr-defined]
    assert "decision" in labels


def test_candidate_metrics_handles_none():
    candidate = DecisionCandidate(asin="A1", vendor_id=1, cost=None, roi_pct=None)
    result = service._candidate_metrics(candidate)  # type: ignore[attr-defined]
    assert result == {}


def test_evaluate_candidate_branches():
    observe = DecisionCandidate(asin="A2", vendor_id=None, cost=10, roi_pct=20, observe_only=True)
    assert service._evaluate_candidate(observe)  # type: ignore[attr-defined]

    none_roi = DecisionCandidate(asin="A3", vendor_id=None, cost=10, roi_pct=None)
    assert service._evaluate_candidate(none_roi) is None  # type: ignore[attr-defined]

    bad_roi = DecisionCandidate(asin="A4", vendor_id=None, cost=10, roi_pct=-10)
    assert service._evaluate_candidate(bad_roi)  # type: ignore[attr-defined]

    ok_roi = DecisionCandidate(asin="A5", vendor_id=None, cost=10, roi_pct=25)
    assert service._evaluate_candidate(ok_roi) is None  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_generate_tasks_records_metrics(monkeypatch, fake_db_session):
    metrics_stub = _StubMetric()
    monkeypatch.setattr(service, "DECISION_ENGINE_LATENCY_SECONDS", metrics_stub)
    monkeypatch.setattr(service, "DECISION_TASKS_CREATED_TOTAL", metrics_stub)
    monkeypatch.setattr(service, "DECISION_INBOX_SIZE", metrics_stub)
    monkeypatch.setattr(service, "DECISION_TASKS_RESOLVED_TOTAL", metrics_stub)

    candidate = DecisionCandidate(asin="A6", vendor_id=2, cost=10, roi_pct=-6)

    async def _fake_fetch(*_args, **_kwargs):
        return [candidate]

    monkeypatch.setattr(service.repository, "fetch_decision_candidates", _fake_fetch)
    fixed_now = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
    monkeypatch.setattr(service, "_now", lambda: fixed_now)

    async def _fake_upsert(_session, plans, now):
        return [
            service.DecisionTaskRecord.from_mapping(
                {
                    "id": "t-metric",
                    "source": "decision_engine",
                    "entity": {"asin": plans[0].asin},
                    "decision": plans[0].decision,
                    "priority": plans[0].priority,
                    "state": "pending",
                    "why": [],
                    "alternatives": [],
                    "created_at": now,
                    "updated_at": now,
                }
            )
        ]

    monkeypatch.setattr(service.repository, "upsert_tasks", _fake_upsert)

    async def _fake_summary(*_args, **_kwargs):
        return {"pending": 1}

    monkeypatch.setattr(service.repository, "summarize_states", _fake_summary)

    session = fake_db_session()
    saved, planned, _count = await service.generate_tasks(session, dry_run=False)
    assert planned
    assert saved
