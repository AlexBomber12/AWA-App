from __future__ import annotations

from dataclasses import dataclass

from awa_common import telegram


@dataclass
class _StubResponse:
    status_code: int
    payload: dict
    text: str = ""

    def json(self) -> dict:
        return self.payload


class _StubClient:
    def __init__(self, response: _StubResponse) -> None:
        self._response = response
        self.requested_url: str | None = None

    def get(self, url: str):
        self.requested_url = url
        return self._response


def test_validate_config_rejects_invalid_token_format() -> None:
    ok, reason = telegram.validate_config("bad-token", "123")
    assert ok is False
    assert "format" in reason


def test_validate_config_accepts_negative_chat_id() -> None:
    client = _StubClient(_StubResponse(status_code=200, payload={"ok": True, "result": {"username": "alertbot"}}))
    ok, reason = telegram.validate_config("123456:ABCDEFGHIJKLMNO", "-987654", client=client)
    assert ok is True
    assert "connected" in reason
    assert client.requested_url == "https://api.telegram.org/bot123456:ABCDEFGHIJKLMNO/getMe"


def test_validate_config_handles_http_error() -> None:
    client = _StubClient(_StubResponse(status_code=401, payload={"ok": False, "description": "Unauthorized"}))
    ok, reason = telegram.validate_config("123456:ABCDEFGHIJKLMNO", "42", client=client)
    assert ok is False
    assert "HTTP 401" in reason or "error" in reason.lower()


def test_validate_config_uses_default_client(monkeypatch) -> None:
    response = _StubResponse(status_code=200, payload={"ok": True, "result": {"first_name": "bot"}})
    created = {"closed": False}

    class DummyClient:
        def __init__(self, timeout):
            self.timeout = timeout

        def get(self, url: str):
            return response

        def close(self):
            created["closed"] = True

    monkeypatch.setattr(telegram.httpx, "Client", DummyClient)
    monkeypatch.setattr(telegram.httpx, "Timeout", lambda *args, **kwargs: ("timeout", args, kwargs))
    ok, reason = telegram.validate_config("99999:ABCDEFGHIJKLMNO", "42", client=None)
    assert ok is True
    assert "configuration valid" in reason or "connected" in reason
    assert created["closed"] is True
