from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from services.alert_bot import worker as alerts_worker
from services.alert_bot.rules_store import RuleConfig


@pytest.mark.asyncio
async def test_evaluate_rules_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(alerts_worker.settings, "ALERTS_ENABLED", False)
    summary = await alerts_worker.evaluate_alert_rules()
    assert summary["rules_total"] == 0
    assert summary["notifications_sent"] == 0


@pytest.mark.asyncio
async def test_evaluate_rules_trigger_and_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(alerts_worker.settings, "ALERTS_ENABLED", True)

    rules = [
        RuleConfig(key="roi", enabled=True, channels={"telegram": True}, schedule_cron="* * * * *"),
        RuleConfig(key="buybox_drop_pct", enabled=True, channels={"telegram": True}),
        RuleConfig(key="returns_rate_pct", enabled=True, channels={"telegram": True}, schedule_cron="0 0 1 1 *"),
    ]

    class DummyStore:
        def list_rules(self) -> list[RuleConfig]:
            return rules

    async def runner_ok(thresholds: dict[str, Any]):
        return alerts_worker.RuleEvaluation(events=2, messages=["first", "second"])

    async def runner_error(thresholds: dict[str, Any]):
        raise RuntimeError("boom")

    async def runner_skip(thresholds: dict[str, Any]):
        return alerts_worker.RuleEvaluation(events=0, messages=[])

    monkeypatch.setattr(alerts_worker, "RULES_STORE", DummyStore())
    monkeypatch.setitem(alerts_worker._RULE_HANDLERS, "roi", alerts_worker.RuleHandler("roi", runner_ok))
    monkeypatch.setitem(
        alerts_worker._RULE_HANDLERS, "buybox_drop_pct", alerts_worker.RuleHandler("buybox_drop_pct", runner_error)
    )
    monkeypatch.setitem(
        alerts_worker._RULE_HANDLERS, "returns_rate_pct", alerts_worker.RuleHandler("returns_rate_pct", runner_skip)
    )

    sent_messages: list[str] = []

    async def fake_send(text: str, **kwargs):
        sent_messages.append(text)
        return True

    monkeypatch.setattr(alerts_worker, "send_message", fake_send)
    monkeypatch.setattr(alerts_worker, "TELEGRAM_ENABLED", True)

    now = datetime(2024, 1, 2, 1, 0, tzinfo=UTC)
    summary = await alerts_worker.evaluate_alert_rules(now=now)

    assert summary["triggered"] == 1
    assert summary["notifications_sent"] == 2
    assert sent_messages == ["first", "second"]


@pytest.mark.asyncio
async def test_dispatch_notifications_channel_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    summary = {"notifications_sent": 0, "notifications_failed": 0}
    rule = RuleConfig(key="roi", enabled=True, channels={"telegram": False})
    await alerts_worker._dispatch_notifications(rule, alerts_worker.RuleEvaluation(1, ["msg"]), summary)
    assert summary["notifications_failed"] == 1


@pytest.mark.asyncio
async def test_dispatch_notifications_telegram_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    summary = {"notifications_sent": 0, "notifications_failed": 0}
    rule = RuleConfig(key="roi", enabled=True, channels={"telegram": True})
    monkeypatch.setattr(alerts_worker, "TELEGRAM_ENABLED", False)
    monkeypatch.setattr(alerts_worker, "_TELEGRAM_REASON", "disabled")
    await alerts_worker._dispatch_notifications(rule, alerts_worker.RuleEvaluation(1, ["msg"]), summary)
    assert summary["notifications_failed"] == 1


@pytest.mark.asyncio
async def test_dispatch_notifications_send_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    summary = {"notifications_sent": 0, "notifications_failed": 0}
    rule = RuleConfig(key="roi", enabled=True, channels={"telegram": True})
    monkeypatch.setattr(alerts_worker, "TELEGRAM_ENABLED", True)
    outcomes = iter([True, False])

    async def fake_send(msg: str, **kwargs) -> bool:
        return next(outcomes)

    monkeypatch.setattr(alerts_worker, "send_message", fake_send)
    await alerts_worker._dispatch_notifications(rule, alerts_worker.RuleEvaluation(2, ["ok", "fail"]), summary)
    assert summary["notifications_sent"] == 1
    assert summary["notifications_failed"] == 1


def test_cron_matches_helper() -> None:
    now = datetime(2024, 1, 1, 15, 0, tzinfo=UTC)
    assert alerts_worker._cron_matches("*/15 * * * *", now)
    assert not alerts_worker._cron_matches("0 0 1 1 *", now)


def test_build_store_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(alerts_worker.settings, "ALERT_RULES_SOURCE", "db")
    store = alerts_worker._build_store()
    from services.alert_bot.worker import DbRulesStore

    assert isinstance(store, DbRulesStore)


def test_load_rules_handles_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenStore:
        def list_rules(self):
            raise ValueError("boom")

    monkeypatch.setattr(alerts_worker, "RULES_STORE", BrokenStore())
    rules = alerts_worker._load_rules()
    assert isinstance(rules, list) and rules
