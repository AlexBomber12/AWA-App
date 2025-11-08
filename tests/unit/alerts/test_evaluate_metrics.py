from __future__ import annotations

import pytest

from services.alert_bot import worker as alerts_worker
from services.alert_bot.rules_store import RuleConfig


class StubCounter:
    def __init__(self) -> None:
        self.records: list[dict[str, str]] = []
        self._labels: dict[str, str] = {}

    def labels(self, **labels: str):
        self._labels = labels
        return self

    def inc(self, *_args, **_kwargs):
        self.records.append(dict(self._labels))


class StubHistogram:
    def __init__(self) -> None:
        self.records: list[dict[str, str]] = []

    def labels(self, **labels: str):
        self.records.append(labels)
        return self

    def observe(self, _value: float) -> None:
        return None


@pytest.mark.asyncio
async def test_evaluate_rules_records_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    rules = [
        RuleConfig(key="roi", enabled=True, channels={"telegram": True}),
        RuleConfig(key="buybox_drop_pct", enabled=True, channels={"telegram": True}),
    ]

    class DummyStore:
        def list_rules(self) -> list[RuleConfig]:
            return rules

    async def trigger_runner(_thresholds):
        return alerts_worker.RuleEvaluation(events=1, messages=["triggered"])

    async def skip_runner(_thresholds):
        return alerts_worker.RuleEvaluation(events=0, messages=[])

    monkeypatch.setattr(alerts_worker, "RULES_STORE", DummyStore())
    monkeypatch.setitem(alerts_worker._RULE_HANDLERS, "roi", alerts_worker.RuleHandler("roi", trigger_runner))
    monkeypatch.setitem(
        alerts_worker._RULE_HANDLERS, "buybox_drop_pct", alerts_worker.RuleHandler("buybox_drop_pct", skip_runner)
    )
    monkeypatch.setattr(alerts_worker, "TELEGRAM_ENABLED", True)

    counter = StubCounter()
    histogram = StubHistogram()
    monkeypatch.setattr(alerts_worker, "ALERTS_RULE_EVALUATIONS_TOTAL", counter)
    monkeypatch.setattr(alerts_worker, "ALERTS_RULE_DURATION_SECONDS", histogram)

    sent: list[str] = []

    async def fake_send_message(text: str, **kwargs):
        sent.append(text)
        return True

    monkeypatch.setattr(alerts_worker, "send_message", fake_send_message)

    summary = await alerts_worker.evaluate_alert_rules()
    assert summary["triggered"] == 1
    assert summary["notifications_sent"] == 1

    assert any(record["rule"] == "roi" and record["result"] == "triggered" for record in counter.records)
    assert any(record["rule"] == "buybox_drop_pct" and record["result"] == "skipped" for record in counter.records)
