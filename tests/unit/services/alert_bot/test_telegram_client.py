from __future__ import annotations

import types
from typing import Any

import httpx
import pytest

from awa_common import telegram


class StubResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> dict[str, Any]:
        if self._payload is None:
            raise ValueError("invalid json")
        return self._payload

    async def aclose(self) -> None:  # pragma: no cover - simple stub
        return None


class StubAsyncClient:
    def __init__(self, responses: list[StubResponse | Exception]) -> None:
        self._responses = responses
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def post(self, url: str, json: dict[str, Any]):
        self.calls.append((url, json))
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.mark.asyncio
async def test_send_message_handles_retry_after() -> None:
    stub_client = StubAsyncClient(
        [
            StubResponse(
                429,
                payload={"ok": False, "description": "slow down", "parameters": {"retry_after": 2}},
            )
        ]
    )
    client = telegram.AsyncTelegramClient(
        token="12345:ABCDE",
        client=stub_client,
        max_concurrency=1,
        max_rps=None,
        max_chat_rps=None,
    )
    result = await client.send_message(chat_id=10, text="hello")
    assert result.status == "retry"
    assert result.retry_after == 2


@pytest.mark.asyncio
async def test_send_message_success_payload() -> None:
    stub_client = StubAsyncClient([StubResponse(200, payload={"ok": True})])
    client = telegram.AsyncTelegramClient(token="12345:ABCDE", client=stub_client)
    result = await client.send_message(chat_id=42, text="ok", parse_mode="Markdown")
    assert result.ok is True
    assert stub_client.calls[0][1]["disable_web_page_preview"] is True
    assert stub_client.calls[0][1]["chat_id"] == 42


class DummyBucket:
    def __init__(self) -> None:
        self.calls = 0

    async def acquire(self) -> None:
        self.calls += 1


@pytest.mark.asyncio
async def test_rate_limiter_invoked(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_client = StubAsyncClient([StubResponse(200, payload={"ok": True})])
    client = telegram.AsyncTelegramClient(token="12345:ABCDE", client=stub_client, max_rps=None, max_chat_rps=None)
    global_bucket = DummyBucket()
    chat_bucket = DummyBucket()
    client._global_bucket = global_bucket  # type: ignore[attr-defined]
    client._per_chat_rate = 1.0  # type: ignore[attr-defined]

    async def fake_get_bucket(self, chat_key: str):
        return chat_bucket

    monkeypatch.setattr(client, "_get_or_create_chat_bucket", types.MethodType(fake_get_bucket, client))

    await client.send_message(chat_id=77, text="limited")
    assert global_bucket.calls == 1
    assert chat_bucket.calls == 1


@pytest.mark.asyncio
async def test_token_bucket_zero_rate(monkeypatch: pytest.MonkeyPatch) -> None:
    bucket = telegram._TokenBucket(0)  # type: ignore[attr-defined]
    called = {"sleep": False}

    async def fake_sleep(_duration: float) -> None:
        called["sleep"] = True

    monkeypatch.setattr(telegram.asyncio, "sleep", fake_sleep)
    await bucket.acquire()
    assert called["sleep"] is False


@pytest.mark.asyncio
async def test_token_bucket_waits(monkeypatch: pytest.MonkeyPatch) -> None:
    bucket = telegram._TokenBucket(1)  # type: ignore[attr-defined]
    bucket.tokens = 0
    sleeps: list[float] = []

    async def fake_sleep(duration: float) -> None:
        sleeps.append(duration)

    monkeypatch.setattr(telegram.asyncio, "sleep", fake_sleep)
    await bucket.acquire()
    assert sleeps  # ensured wait branch executed


def test_retry_after_from_payload() -> None:
    assert telegram._retry_after_from_payload({"parameters": {"retry_after": 3}}) == 3.0  # type: ignore[attr-defined]
    assert telegram._retry_after_from_payload({}) is None  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_send_message_missing_token() -> None:
    stub_client = StubAsyncClient([])
    client = telegram.AsyncTelegramClient(token="", client=stub_client)
    result = await client.send_message(chat_id=1, text="hi")
    assert result.ok is False
    assert result.status == "error"


@pytest.mark.asyncio
async def test_send_message_invalid_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_client = StubAsyncClient([])
    client = telegram.AsyncTelegramClient(token="12345:ABCDE", client=stub_client)
    result = await client.send_message(chat_id="   ", text="hi")
    assert result.ok is False
    assert result.status == "error"


@pytest.mark.asyncio
async def test_get_me_and_get_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        StubResponse(200, payload={"ok": True, "result": {"username": "bot"}}),
        StubResponse(200, payload={"ok": True, "result": {"id": 1}}),
    ]
    stub_client = StubAsyncClient(responses)
    client = telegram.AsyncTelegramClient(token="12345:ABCDE", client=stub_client)
    me = await client.get_me()
    assert me.ok is True
    chat = await client.get_chat(123)
    assert chat.ok is True


@pytest.mark.asyncio
async def test_aclose_closes_owned_client() -> None:
    client = telegram.AsyncTelegramClient(token="12345:ABCDE")

    class DummyClient:
        def __init__(self) -> None:
            self.closed = False

        async def aclose(self) -> None:
            self.closed = True

    dummy = DummyClient()
    client._client = dummy  # type: ignore[attr-defined]
    client._owns_client = True  # type: ignore[attr-defined]
    await client.aclose()
    assert dummy.closed is True


@pytest.mark.asyncio
async def test_send_message_sets_disable_notification() -> None:
    stub_client = StubAsyncClient([StubResponse(200, payload={"ok": True})])
    client = telegram.AsyncTelegramClient(token="12345:ABCDE", client=stub_client)
    await client.send_message(chat_id=1, text="hi", disable_notification=False)
    assert stub_client.calls[0][1]["disable_notification"] is False


@pytest.mark.asyncio
async def test_request_handles_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class RaisingClient:
        async def post(self, url, json):
            raise httpx.RequestError("boom", request=httpx.Request("POST", url))

    client = telegram.AsyncTelegramClient(token="12345:ABCDE", client=RaisingClient())
    response = await client._request("sendMessage", payload={})  # type: ignore[attr-defined]
    assert response.ok is False
    assert "RequestError" in (response.description or "")


@pytest.mark.asyncio
async def test_request_handles_invalid_json() -> None:
    class InvalidJsonResponse(StubResponse):
        def json(self) -> dict[str, Any]:
            raise ValueError("bad")

    stub_client = StubAsyncClient([InvalidJsonResponse(200, payload=None, text="raw")])
    client = telegram.AsyncTelegramClient(token="12345:ABCDE", client=stub_client)
    response = await client._request("sendMessage", payload={})  # type: ignore[attr-defined]
    assert response.ok is True
    assert response.payload is None


def test_coerce_chat_id_returns_string() -> None:
    client = telegram.AsyncTelegramClient(token="12345:ABCDE", client=StubAsyncClient([]))
    value, reason = client._coerce_chat_id("@channel")  # type: ignore[attr-defined]
    assert value == "@channel"
    assert reason is None
