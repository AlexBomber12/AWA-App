from __future__ import annotations

import types
from datetime import UTC, datetime, timedelta
from pathlib import Path

from services.alert_bot import config as alert_config, worker
from services.alert_bot.config import AlertRule
from services.alert_bot.rules import AlertEvent


def _sample_rule(rule_id: str, schedule: str | None = None) -> AlertRule:
    return AlertRule(
        id=rule_id,
        type="roi_drop",
        enabled=True,
        schedule=schedule,
        chat_ids=["@ops"],
        parse_mode="HTML",
        params={},
        template=None,
    )


def test_rule_scheduler_every_intervals() -> None:
    scheduler = worker.RuleScheduler()
    rule = _sample_rule("roi_drop", schedule="@every 5m")
    now = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    due_once = scheduler.due_rules([rule], now=now)
    assert due_once == [rule]
    not_due = scheduler.due_rules([rule], now=now)
    assert not not_due
    later = now + timedelta(minutes=5)
    due_again = scheduler.due_rules([rule], now=later)
    assert due_again == [rule]


def test_rule_scheduler_cron_matches() -> None:
    scheduler = worker.RuleScheduler()
    rule = _sample_rule("roi_drop", schedule="*/5 * * * *")
    now = datetime(2024, 1, 1, 12, 10, tzinfo=UTC)
    due = scheduler.due_rules([rule], now=now)
    assert due == [rule]
    not_due = scheduler.due_rules([rule], now=now + timedelta(minutes=1))
    assert not not_due


def test_rule_scheduler_invalid_cron_logs_once(monkeypatch) -> None:
    scheduler = worker.RuleScheduler()
    rule = _sample_rule("roi_drop", schedule="bad cron")
    now = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    calls: list[tuple[tuple, dict]] = []

    def fake_warning(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(worker, "logger", types.SimpleNamespace(warning=fake_warning))

    assert not scheduler.due_rules([rule], now=now)
    assert calls and calls[0][1]["rule"] == "roi_drop"
    calls.clear()
    assert not scheduler.due_rules([rule], now=now + timedelta(minutes=5))
    assert not calls  # cached invalid cron should not log again


def test_dedupe_events_keeps_first() -> None:
    events = [
        AlertEvent(rule_id="roi", chat_ids=["@ops"], text="first", dedupe_key="a"),
        AlertEvent(rule_id="roi", chat_ids=["@ops"], text="second", dedupe_key="a"),
        AlertEvent(rule_id="roi", chat_ids=["@ops"], text="unique", dedupe_key="b"),
    ]
    deduped = worker._dedupe_events(events)
    assert [event.text for event in deduped] == ["first", "unique"]


def test_collect_chat_ids_prefers_runtime() -> None:
    rule = alert_config.AlertRule(
        id="roi",
        type="roi_drop",
        enabled=True,
        schedule=None,
        chat_ids=["@ops"],
        parse_mode="HTML",
        params={},
        template=None,
    )
    defaults = alert_config.AlertRuleDefaults(enabled=True, parse_mode="HTML", chat_ids=["@ops"])
    runtime = alert_config.AlertRulesRuntime(
        version="1", defaults=defaults, rules=[rule], source_path=Path("x"), loaded_at=0.0
    )
    ids = worker._collect_chat_ids(runtime, [])
    assert ids == {"@ops"}
