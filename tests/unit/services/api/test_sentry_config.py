from types import SimpleNamespace

import services.api.sentry_config as sentry_config


def test_scrub_mapping_masks_sensitive_fields():
    data = {
        "password": "secret",
        "token": "abc",
        "nested": {"api_key": "xyz"},
        "list": ["keep"],
    }
    scrubbed = sentry_config._scrub_mapping(data)
    assert scrubbed["password"] == "[redacted]"
    assert scrubbed["token"] == "[redacted]"
    assert scrubbed["nested"]["api_key"] == "[redacted]"


def test_before_send_adds_request_id(monkeypatch):
    event = {
        "request": {
            "headers": {"x-request-id": "abc", "Authorization": "secret"},
            "data": {"password": "hidden"},
        },
        "extra": {"token": "abc"},
    }
    monkeypatch.setattr(
        sentry_config, "correlation_id", SimpleNamespace(get=lambda: "fallback")
    )
    result = sentry_config.before_send(event, {})
    assert result["request"]["headers"]["Authorization"] == "[redacted]"
    assert result["request"]["data"]["password"] == "[redacted]"
    assert result["tags"]["request_id"] == "abc"
    assert result["extra"]["token"] == "[redacted]"


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
