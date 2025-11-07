import services.api.sentry_config as sentry_config


def test_before_send_adds_request_id_and_masks():
    event = {
        "request": {
            "headers": {"x-request-id": "abc", "Authorization": "secret"},
            "data": {"password": "hidden"},
        },
        "extra": {"token": "abc"},
    }
    result = sentry_config.before_send(event, {})
    assert result is not event
    assert result["request"]["headers"]["Authorization"] == "***"
    assert result["request"]["data"]["password"] == "***"
    assert result["tags"]["request_id"] == "abc"
    assert result["extra"]["token"] == "***"
    assert event["request"]["headers"]["Authorization"] == "secret"


def test_init_sentry_if_configured_invokes_sdk(monkeypatch, settings_env):
    captured = {}
    settings_env.SENTRY_DSN = "https://dsn.example/1"
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "0.5")
    monkeypatch.setenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")

    def fake_init(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(sentry_config.sentry_sdk, "init", fake_init)
    sentry_config.init_sentry_if_configured()
    assert captured["dsn"] == "https://dsn.example/1"
    assert captured["before_send"] is sentry_config.before_send
    assert captured["before_breadcrumb"] is sentry_config.before_breadcrumb
