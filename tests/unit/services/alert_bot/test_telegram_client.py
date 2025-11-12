from __future__ import annotations

import types
from typing import Any

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
