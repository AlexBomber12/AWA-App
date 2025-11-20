from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from awa_common import telegram
from services.alert_bot import config as alert_config, worker
from services.alert_bot.decider import NotificationIntent
from services.alert_bot.rules import AlertEvent
from services.alert_bot.settings import AlertBotSettings


def _make_runtime() -> alert_config.AlertRulesRuntime:
    rule = alert_config.AlertRule(
        id="roi_drop",
        type="roi_drop",
        enabled=True,
        schedule=None,
        chat_ids=["@ops"],
        parse_mode="HTML",
        params={},
        template=None,
    )
    defaults = alert_config.AlertRuleDefaults(enabled=True, parse_mode="HTML", chat_ids=["@ops"])
    return alert_config.AlertRulesRuntime(
        version="1", defaults=defaults, rules=[rule], source_path=Path("x"), loaded_at=0.0
    )


def _settings(**overrides: object) -> AlertBotSettings:
    base = AlertBotSettings(
        enabled=True,
        telegram_token="12345:ABCDEabcde",
        default_chat_id="@ops",
        evaluation_cron="*/5 * * * *",
        send_cron="*/1 * * * *",
        eval_concurrency=1,
        send_concurrency=1,
        rule_timeout_s=0.01,
        env="test",
        service_name="alert_bot",
        version="test",
    )
    return base.model_copy(update=overrides)


class _StubTransport:
    def __init__(self, results: list[telegram.TelegramSendResult] | None = None) -> None:
        self.calls: list[tuple[str, NotificationIntent]] = []
        self._results = results or []
        self.validations: list[set[str]] = []
        self.validation_result: tuple[bool, str | None] = (True, None)

    async def send(self, chat_id: str, intent: NotificationIntent) -> telegram.TelegramSendResult:
        self.calls.append((chat_id, intent))
        if self._results:
            return self._results.pop(0)
        return telegram.TelegramSendResult(ok=True, status="ok", response=None)  # type: ignore[attr-defined]

    async def validate(self, chat_ids: set[str]) -> tuple[bool, str | None]:
        self.validations.append(chat_ids)
        return self.validation_result


def _runner(
    *, settings: AlertBotSettings | None = None, transport: _StubTransport | None = None
) -> worker.AlertBotRunner:
    return worker.AlertBotRunner(settings=settings or _settings(), transport=transport or _StubTransport())


@pytest.mark.asyncio
async def test_runner_disabled() -> None:
    runner = _runner(settings=_settings(enabled=False))
    result = await runner.run()
    assert result["rules_total"] == 0


@pytest.mark.asyncio
async def test_runner_processes_events(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _make_runtime()
    transport = _StubTransport(
        [
            telegram.TelegramSendResult(ok=True, status="ok", response=None)  # type: ignore[attr-defined]
        ]
    )
    runner = _runner(transport=transport)
    monkeypatch.setattr(runner, "_load_config", lambda: runtime)

    async def fake_validate(_runtime, _intents):
        runner._sending_enabled = True
        runner._degraded_reason = None

    monkeypatch.setattr(runner, "_ensure_validation", fake_validate)

    async def fake_evaluate(_rule):
        return [
            AlertEvent(rule_id="roi_drop", chat_ids=["@ops"], text="hi", dedupe_key="k"),
            AlertEvent(rule_id="roi_drop", chat_ids=["@ops"], text="hi", dedupe_key="k"),
        ]

    monkeypatch.setattr(worker, "evaluate_rule", fake_evaluate)

    result = await runner.run(now=datetime(2024, 1, 1, tzinfo=UTC))
    assert result["notifications_sent"] == 1
    assert transport.calls[0][0] == "@ops"


@pytest.mark.asyncio
async def test_dispatch_events_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    retry_response = telegram.TelegramResponse(
        ok=False, status_code=429, payload={}, retry_after=0.01, description="wait", error_code=429
    )  # type: ignore[attr-defined]
    ok_result = telegram.TelegramSendResult(ok=True, status="ok", response=None)  # type: ignore[attr-defined]
    retry_result = telegram.TelegramSendResult(ok=False, status="retry", response=retry_response)  # type: ignore[attr-defined]
    transport = _StubTransport([retry_result, ok_result])
    runner = _runner(transport=transport)
    runner._sending_enabled = True
    runner._degraded_reason = None

    async def fake_sleep(_duration: float) -> None:
        return None

    monkeypatch.setattr(worker.asyncio, "sleep", fake_sleep)

    stats = worker.BatchStats()
    intent = NotificationIntent(
        rule_id="roi_drop",
        severity="info",
        message="hello",
        chat_ids=("@ops",),
        parse_mode="HTML",
        dedupe_key="d",
        disable_web_page_preview=True,
    )
    await runner._dispatch_intents([intent], stats)
    assert stats.messages_sent == 1
    assert stats.retries >= 1


@pytest.mark.asyncio
async def test_dispatch_events_skips_when_disabled() -> None:
    runner = _runner()
    runner._sending_enabled = False
    runner._degraded_reason = "no-token"
    stats = worker.BatchStats()
    intent = NotificationIntent(
        rule_id="roi_drop",
        severity="info",
        message="hello",
        chat_ids=("@ops",),
        parse_mode="HTML",
        dedupe_key="d",
        disable_web_page_preview=True,
    )
    await runner._dispatch_intents([intent], stats)
    assert stats.messages_failed == len(intent.chat_ids)


@pytest.mark.asyncio
async def test_run_validation_success(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _StubTransport()
    runner = _runner(transport=transport)
    await runner._run_validation(frozenset({"@ops"}), "v1")
    assert runner._sending_enabled is True
    assert runner._last_validation_version == "v1"
    assert transport.validations


@pytest.mark.asyncio
async def test_run_validation_chat_failure() -> None:
    transport = _StubTransport()
    transport.validation_result = (False, "chat_invalid:@ops")
    runner = _runner(transport=transport)
    await runner._run_validation(frozenset({"@ops"}), "v1")
    assert runner._sending_enabled is False
    assert runner._degraded_reason.startswith("chat_invalid")


@pytest.mark.asyncio
async def test_run_validation_no_chats() -> None:
    runner = _runner()
    await runner._run_validation(frozenset(), "v1")
    assert runner._sending_enabled is False


@pytest.mark.asyncio
async def test_ensure_validation_skips_when_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _make_runtime()
    runner = _runner()
    runner._sending_enabled = True
    runner._last_validation_version = runtime.version
    runner._last_validated_chat_ids = frozenset(runtime.chat_ids())

    async def boom(*_args, **_kwargs):
        raise AssertionError("should not run")

    monkeypatch.setattr(runner, "_run_validation", boom)
    intent = NotificationIntent(
        rule_id="roi_drop",
        severity="info",
        message="hello",
        chat_ids=("@ops",),
        parse_mode="HTML",
        dedupe_key="k",
        disable_web_page_preview=True,
    )
    await runner._ensure_validation(runtime, [intent])


def test_resolve_rules_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _runner()
    fallback_rule = alert_config.AlertRule(
        id="legacy",
        type="roi_drop",
        enabled=True,
        schedule=None,
        chat_ids=["@ops"],
        parse_mode="HTML",
        params={},
        template=None,
    )
    monkeypatch.setattr(runner, "_legacy_rules", lambda: [])
    monkeypatch.setattr(runner, "_default_rules", lambda: [fallback_rule])
    rules, source = runner._resolve_rules(None)
    assert source == "default"
    assert rules[0].id == "legacy"


def test_load_config_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_a = _make_runtime()
    runtime_b = _make_runtime()
    runtime_b.version = "2"

    class StubManager:
        def __init__(self):
            self.loaded = False

        def get(self):
            return None if not self.loaded else runtime_a

        def load(self, *, force: bool):
            self.loaded = True
            return runtime_a

        def maybe_reload(self):
            return runtime_b

    runner = _runner()
    runner._config_manager = StubManager()  # type: ignore[attr-defined]
    first = runner._load_config()
    assert first is runtime_a
    second = runner._load_config()
    assert second is runtime_b


@pytest.mark.asyncio
async def test_send_intent_failure() -> None:
    fail_response = telegram.TelegramResponse(
        ok=False, status_code=500, payload={}, description="err", error_code=500, retry_after=None
    )  # type: ignore[attr-defined]
    fail_result = telegram.TelegramSendResult(ok=False, status="error", response=fail_response)  # type: ignore[attr-defined]
    transport = _StubTransport([fail_result])
    runner = _runner(transport=transport)
    runner._sending_enabled = True
    stats = worker.BatchStats()
    intent = NotificationIntent(
        rule_id="roi_drop",
        severity="info",
        message="hello",
        chat_ids=("@ops",),
        parse_mode="HTML",
        dedupe_key="d",
        disable_web_page_preview=True,
    )
    await runner._send_intent("@ops", intent, stats)
    assert stats.messages_failed == 1


@pytest.mark.asyncio
async def test_run_no_rules(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _runner()
    monkeypatch.setattr(runner, "_load_config", lambda: None)
    monkeypatch.setattr(runner, "_legacy_rules", lambda: [])
    monkeypatch.setattr(runner, "_default_rules", lambda: [])
    summary = await runner.run(now=datetime(2024, 1, 1, tzinfo=UTC))
    assert summary["rules_total"] == 0
