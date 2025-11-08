from __future__ import annotations

import pytest

from awa_common import metrics
from services.alert_bot import worker as alerts_worker
from services.alert_bot.rules_store import RuleConfig
from services.worker import tasks as worker_tasks

pytestmark = pytest.mark.integration


def test_evaluate_task_handles_disabled(monkeypatch) -> None:
    metrics.ALERTS_NOTIFICATIONS_FAILED_TOTAL.clear()
    metrics.ALERTS_RULE_EVALUATIONS_TOTAL.clear()

    rules = [RuleConfig(key="roi", enabled=True, channels={"telegram": True})]

    class DummyStore:
        def list_rules(self):
            return rules

    async def fake_runner(_thresholds):
        return alerts_worker.RuleEvaluation(events=1, messages=["disabled"])

    async def _should_not_send(*_args, **_kwargs):
        raise AssertionError("send_message should not be called when Telegram is disabled")

    monkeypatch.setattr(alerts_worker, "RULES_STORE", DummyStore())
    monkeypatch.setitem(alerts_worker._RULE_HANDLERS, "roi", alerts_worker.RuleHandler("roi", fake_runner))
    monkeypatch.setattr(alerts_worker, "TELEGRAM_ENABLED", False)
    monkeypatch.setattr(alerts_worker, "_TELEGRAM_REASON", "missing token")
    monkeypatch.setattr(alerts_worker, "send_message", _should_not_send)

    result = worker_tasks.evaluate_alert_rules()
    assert result["notifications_failed"] == 1

    samples = metrics.ALERTS_NOTIFICATIONS_FAILED_TOTAL.collect()[0].samples
    disabled_sample = next(sample for sample in samples if sample.labels["error_type"] == "disabled")
    assert disabled_sample.value == 1.0
