from __future__ import annotations

import asyncio

import pytest

from services.alert_bot import worker
from services.alert_bot.config import AlertRule
from services.alert_bot.rules import AlertEvent


class StubMetric:
    def __init__(self) -> None:
        self.records: list[dict[str, str]] = []
        self.values: list[float] = []

    def labels(self, **labels: str):
        self.records.append(labels)
        return self

    def inc(self, value: float = 1.0) -> None:
        self.values.append(value)

    def observe(self, value: float) -> None:
        self.values.append(value)


def _rule(rule_id: str = "roi") -> AlertRule:
    return AlertRule(
        id=rule_id,
        type="roi_drop",
        enabled=True,
        schedule=None,
        chat_ids=["@ops"],
        parse_mode="HTML",
        params={},
        template=None,
    )


@pytest.mark.asyncio
async def test_evaluate_single_rule_records_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = worker.AlertBotRunner()

    async def fake_evaluate(_rule: AlertRule):
        return [AlertEvent(rule_id=_rule.id, chat_ids=["@ops"], text="ok", dedupe_key="roi:1")]

    metric_counter = StubMetric()
    metric_histogram = StubMetric()
    events_counter = StubMetric()

    monkeypatch.setattr(worker, "evaluate_rule", fake_evaluate)
    monkeypatch.setattr(worker, "ALERTBOT_RULES_EVALUATED_TOTAL", metric_counter)
    monkeypatch.setattr(worker, "ALERTBOT_RULE_EVAL_DURATION_SECONDS", metric_histogram)
    monkeypatch.setattr(worker, "ALERTBOT_EVENTS_EMITTED_TOTAL", events_counter)

    result = await runner._evaluate_single_rule(_rule(), asyncio.Semaphore(1))
    assert result.outcome == "ok"
    assert metric_counter.records and metric_counter.records[0]["rule"] == "roi"
    assert events_counter.records and events_counter.records[0]["rule"] == "roi"


@pytest.mark.asyncio
async def test_evaluate_single_rule_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = worker.AlertBotRunner()

    async def slow_rule(_rule: AlertRule):
        await asyncio.Future()

    metric_counter = StubMetric()
    metric_histogram = StubMetric()
    monkeypatch.setattr(worker, "evaluate_rule", slow_rule)
    monkeypatch.setattr(worker.settings, "ALERT_RULE_TIMEOUT_S", 0.01)
    monkeypatch.setattr(worker, "ALERTBOT_RULES_EVALUATED_TOTAL", metric_counter)
    monkeypatch.setattr(worker, "ALERTBOT_RULE_EVAL_DURATION_SECONDS", metric_histogram)

    result = await runner._evaluate_single_rule(_rule("slow"), asyncio.Semaphore(1))
    assert result.outcome == "timeout"
    assert metric_counter.records[-1]["outcome"] == "timeout"
