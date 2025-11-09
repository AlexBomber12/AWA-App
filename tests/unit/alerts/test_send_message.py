from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from awa_common import telegram
from awa_common.logging import configure_logging

configure_logging(service="tests-alerts")  # ensure structlog bridges to stdlib logging for caplog


class DummyResponse:
    def __init__(self, status_code: int, text: str = "", payload: dict | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self._payload = payload

    def json(self) -> dict:
        if self._payload is None:
            raise ValueError("invalid json")
        return self._payload


class DummyClient:
    def __init__(self, response: DummyResponse, *, raise_exc: bool = False) -> None:
        self._response = response
        self._raise_exc = raise_exc
        self.requests: list[tuple[str, dict[str, object]]] = []
        self._request = httpx.Request("POST", "https://api.telegram.org/botTEST/sendMessage")

    async def post(self, url: str, json: dict[str, object]):
        self.requests.append((url, json))
        if self._raise_exc:
            raise httpx.TimeoutException("boom", request=self._request)
        return self._response


@pytest.fixture(autouse=True)
def _reset_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(telegram.settings, "TELEGRAM_TOKEN", "123456:ABCDEFGHIJKLMNO")
    monkeypatch.setattr(telegram.settings, "TELEGRAM_DEFAULT_CHAT_ID", 42)


class StubCounter:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def labels(self, **labels: object):
        self.records.append(labels)
        return self

    def inc(self, *_args, **_kwargs) -> None:
        return None


@pytest.fixture
def metric_stubs(monkeypatch: pytest.MonkeyPatch):
    sent = StubCounter()
    failed = StubCounter()
    monkeypatch.setattr(telegram, "ALERTS_NOTIFICATIONS_SENT_TOTAL", sent)
    monkeypatch.setattr(telegram, "ALERTS_NOTIFICATIONS_FAILED_TOTAL", failed)
    return sent, failed


@pytest.mark.asyncio
async def test_send_message_success(metric_stubs, monkeypatch: pytest.MonkeyPatch) -> None:
    sent_counter, failed_counter = metric_stubs
    client = DummyClient(DummyResponse(status_code=200, payload={"ok": True}))
    ok = await telegram.send_message("hello", client=client, rule="roi")
    assert ok is True
    assert sent_counter.records
    assert sent_counter.records[0]["rule"] == "roi"
    assert not failed_counter.records


@pytest.mark.asyncio
async def test_send_message_http_error(metric_stubs) -> None:
    sent_counter, failed_counter = metric_stubs
    client = DummyClient(DummyResponse(status_code=400, text="bad request"))
    ok = await telegram.send_message("oops", client=client, rule="roi")
    assert ok is False
    assert failed_counter.records[0]["error_type"] == "http_error"
    assert not sent_counter.records


@pytest.mark.asyncio
async def test_send_message_exception(metric_stubs) -> None:
    sent_counter, failed_counter = metric_stubs
    client = DummyClient(DummyResponse(status_code=200, payload={"ok": True}), raise_exc=True)
    ok = await telegram.send_message("timeout", client=client, rule="roi")
    assert ok is False
    assert failed_counter.records[0]["error_type"] == "exception"
    assert not sent_counter.records


@pytest.mark.asyncio
async def test_send_message_api_error(metric_stubs) -> None:
    sent_counter, failed_counter = metric_stubs
    client = DummyClient(DummyResponse(status_code=200, payload={"ok": False, "description": "forbidden"}))
    ok = await telegram.send_message("blocked", client=client, rule="roi")
    assert ok is False
    assert failed_counter.records[0]["error_type"] == "api_error"
    assert not sent_counter.records


@pytest.mark.asyncio
async def test_send_message_invalid_json(metric_stubs) -> None:
    sent_counter, failed_counter = metric_stubs
    client = DummyClient(DummyResponse(status_code=200, text="oops", payload=None))
    ok = await telegram.send_message("broken", client=client, rule="roi")
    assert ok is False
    assert failed_counter.records[0]["error_type"] == "invalid_response"
    assert not sent_counter.records


def test_normalize_chat_id_str() -> None:
    value, reason = telegram._normalize_chat_id(" 77 ")
    assert value == 77
    assert reason is None


def test_normalize_chat_id_non_numeric() -> None:
    value, reason = telegram._normalize_chat_id("abc")
    assert value is None
    assert "integer" in (reason or "")


@pytest.mark.asyncio
async def test_send_photo_and_document_forward_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[tuple[str, dict[str, Any]]] = []

    async def fake_send_payload(method: str, payload: dict[str, Any], **kwargs):
        captured.append((method, payload))
        return True

    monkeypatch.setattr(telegram, "_send_payload", fake_send_payload)

    await telegram.send_photo("http://img", caption="cap", chat_id=7, rule="roi")
    await telegram.send_document("doc-id", caption=None, rule="roi")

    assert captured[0][0] == "sendPhoto"
    assert captured[0][1]["photo"] == "http://img"
    assert captured[1][0] == "sendDocument"
    assert captured[1][1]["document"] == "doc-id"


@pytest.mark.asyncio
async def test_ensure_async_client_reuses_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyClient:
        def __init__(self, timeout):
            self.timeout = timeout

    created: list[DummyClient] = []

    async def fake_lock():
        pass

    monkeypatch.setattr(telegram, "_ASYNC_CLIENT", None, raising=False)
    monkeypatch.setattr(telegram, "_ASYNC_CLIENT_LOCK", asyncio.Lock(), raising=False)
    monkeypatch.setattr(
        telegram.httpx,
        "AsyncClient",
        lambda timeout: created.append(DummyClient(timeout)) or created[-1],
    )

    client1 = await telegram._ensure_async_client()
    client2 = await telegram._ensure_async_client()

    assert client1 is client2
    assert created  # ensure factory invoked once


@pytest.mark.asyncio
async def test_send_payload_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(telegram.settings, "TELEGRAM_TOKEN", "12345:ABCDE")
    monkeypatch.setattr(telegram.settings, "TELEGRAM_DEFAULT_CHAT_ID", 555)

    class DummyClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        async def post(self, url: str, json: dict[str, Any]):
            self.calls.append((url, json))
            return DummyResponse(status_code=200, payload={"ok": True})

    client = DummyClient()
    ok = await telegram._send_payload(
        method="sendMessage",
        payload={"text": "hi"},
        chat_id_override=None,
        disable_notification=True,
        client=client,
        rule="roi",
    )
    assert ok is True
    assert client.calls[0][1]["chat_id"] == 555
    assert client.calls[0][1]["disable_notification"] is True
