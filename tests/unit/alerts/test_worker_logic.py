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


def test_build_store_unsupported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(alerts_worker.settings, "ALERT_RULES_SOURCE", "unknown")
    store = alerts_worker._build_store()
    from services.alert_bot.rules_store import FileRulesStore

    assert isinstance(store, FileRulesStore)


def test_load_rules_handles_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenStore:
        def list_rules(self):
            raise ValueError("boom")

    monkeypatch.setattr(alerts_worker, "RULES_STORE", BrokenStore())
    rules = alerts_worker._load_rules()
    assert isinstance(rules, list) and rules


@pytest.mark.asyncio
async def test_revalidate_telegram(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"token": None, "chat": None}

    def fake_validate(token, chat_id):
        called["token"] = token
        called["chat"] = chat_id
        return True, "ok"

    monkeypatch.setattr(alerts_worker, "validate_config", fake_validate)
    monkeypatch.setattr(alerts_worker.settings, "TELEGRAM_TOKEN", "abc")
    monkeypatch.setattr(alerts_worker.settings, "TELEGRAM_DEFAULT_CHAT_ID", 123)
    enabled, reason = alerts_worker.revalidate_telegram(force_log=True)
    assert enabled is True
    assert reason == "ok"


def test_alert_rules_health(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(alerts_worker, "revalidate_telegram", lambda force_log=False: (True, "ok"))
    result = alerts_worker.alert_rules_health()
    assert result["telegram_enabled"] is True


@pytest.mark.asyncio
async def test_run_roi_and_returns_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    async def roi_rows(*args, **kwargs):
        return [{"asin": "A1", "roi_pct": 4.5}]

    async def returns_rows(*args, **kwargs):
        return [{"asin": "B1", "returns_ratio": 7}]

    monkeypatch.setattr(alerts_worker.db_rules, "query_roi_breaches", roi_rows)
    result = await alerts_worker._run_roi({})
    assert result.events == 1
    assert "A1" in result.messages[0]

    monkeypatch.setattr(alerts_worker.db_rules, "query_high_returns", returns_rows)
    returns = await alerts_worker._run_returns({})
    assert returns.events == 1
    assert "B1" in returns.messages[0]


def test_threshold_helpers_and_format() -> None:
    assert alerts_worker._threshold_int({}, "foo", 3) == 3
    assert alerts_worker._threshold_float({"bar": "2.5"}, "bar", 1.0) == 2.5
    assert alerts_worker._format_number(3.14159) == "3.14"
    assert alerts_worker._format_number(5) == "5"
