import pytest

from services.api.sentry_config import before_send

pytestmark = pytest.mark.integration


def test_before_send_scrubs_pii():
    event = {
        "request": {
            "headers": {
                "Authorization": "Bearer SECRET",
                "X-Other": "ok",
                "Cookie": "a=b",
            },
            "data": {"password": "123", "email": "a@b.c", "keep": "ok"},
        },
        "user": {"email": "user@example.com", "id": "42"},
        "extra": {"token": "XYZ", "keep": "ok"},
    }
    red = before_send(event, hint=None)
    req = red["request"]
    assert req["headers"]["Authorization"] == "***"
    assert req["headers"]["Cookie"] == "***"
    assert req["headers"]["X-Other"] == "ok"
    assert req["data"]["password"] == "***"
    assert req["data"]["email"] == "***"
    assert req["data"]["keep"] == "ok"
    assert red["user"]["email"] == "***"
    assert red["extra"]["token"] == "***"
    assert red["extra"]["keep"] == "ok"
