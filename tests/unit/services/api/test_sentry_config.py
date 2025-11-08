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


def test_init_sentry_if_configured_invokes_common(monkeypatch):
    called = {}

    def fake_init(service: str) -> None:
        called["service"] = service

    monkeypatch.setattr(sentry_config, "init_sentry", fake_init)
    sentry_config.init_sentry_if_configured()
    assert called["service"] == "api"
