from __future__ import annotations

from datetime import UTC, datetime, timedelta

from services.alert_bot import worker
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


def test_dedupe_events_keeps_first() -> None:
    events = [
        AlertEvent(rule_id="roi", chat_ids=["@ops"], text="first", dedupe_key="a"),
        AlertEvent(rule_id="roi", chat_ids=["@ops"], text="second", dedupe_key="a"),
        AlertEvent(rule_id="roi", chat_ids=["@ops"], text="unique", dedupe_key="b"),
    ]
    deduped = worker._dedupe_events(events)
    assert [event.text for event in deduped] == ["first", "unique"]
