import types

import pytest

from services.alert_bot import worker
from services.alert_bot.settings import AlertBotSettings


def _base_settings(**overrides: object) -> AlertBotSettings:
    base = AlertBotSettings(
        enabled=True,
        telegram_token="12345:ABCDEabcde",
        default_chat_id="@ops",
        evaluation_cron="*/5 * * * *",
        send_cron="*/1 * * * *",
        eval_concurrency=1,
        send_concurrency=1,
        rule_timeout_s=0.1,
        env="test",
        service_name="alert_bot",
        version="test",
    )
    return base.model_copy(update=overrides)


def test_validate_runtime_rejects_placeholder_token() -> None:
    settings = _base_settings(telegram_token="changeme")
    ok, reason = settings.validate_runtime()
    assert not ok
    assert "placeholder" in (reason or "")


def test_validate_runtime_requires_chat_id() -> None:
    settings = _base_settings(default_chat_id=None)
    ok, reason = settings.validate_runtime()
    assert not ok
    assert "missing" in (reason or "")


def test_validate_runtime_success() -> None:
    settings = _base_settings()
    ok, reason = settings.validate_runtime()
    assert ok
    assert reason is None


@pytest.mark.asyncio
async def test_validate_startup_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _base_settings(telegram_token="")
    runner = worker.AlertBotRunner(settings=settings)
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        worker,
        "logger",
        types.SimpleNamespace(
            error=lambda *args, **kwargs: calls.append(kwargs),
            info=lambda *args, **kwargs: None,
            warning=lambda *args, **kwargs: None,
        ),
    )
    with pytest.raises(worker.AlertConfigurationError):
        await runner.validate_startup()
    assert any("TELEGRAM_TOKEN" in str(call.get("reason", "")) for call in calls)


@pytest.mark.asyncio
async def test_validate_startup_missing_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _base_settings(default_chat_id=None)
    runner = worker.AlertBotRunner(settings=settings)
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        worker,
        "logger",
        types.SimpleNamespace(
            error=lambda *args, **kwargs: calls.append(kwargs),
            info=lambda *args, **kwargs: None,
            warning=lambda *args, **kwargs: None,
        ),
    )
    with pytest.raises(worker.AlertConfigurationError):
        await runner.validate_startup()
    assert any("TELEGRAM_DEFAULT_CHAT_ID" in str(call.get("reason", "")) for call in calls)
