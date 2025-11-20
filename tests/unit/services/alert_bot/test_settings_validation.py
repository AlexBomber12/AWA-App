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
