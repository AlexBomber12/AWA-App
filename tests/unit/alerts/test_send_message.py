from __future__ import annotations

import httpx
import pytest

from awa_common import telegram
from awa_common.logging import configure_logging

configure_logging(service="tests-alerts")  # ensure structlog bridges to stdlib logging for caplog


class DummyResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


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
    client = DummyClient(DummyResponse(status_code=200))
    ok = await telegram.send_message("hello", client=client, rule="roi")
    assert ok is True
    assert sent_counter.records
    assert sent_counter.records[0]["rule"] == "roi"
    assert not failed_counter.records


@pytest.mark.asyncio
async def test_send_message_http_error(metric_stubs, caplog: pytest.LogCaptureFixture) -> None:
    sent_counter, failed_counter = metric_stubs
    caplog.set_level("ERROR")
    client = DummyClient(DummyResponse(status_code=400, text="bad request"))
    ok = await telegram.send_message("oops", client=client, rule="roi")
    assert ok is False
    assert "telegram.http_error" in caplog.text
    assert failed_counter.records[0]["error_type"] == "http_error"
    assert not sent_counter.records


@pytest.mark.asyncio
async def test_send_message_exception(metric_stubs, caplog: pytest.LogCaptureFixture) -> None:
    sent_counter, failed_counter = metric_stubs
    caplog.set_level("ERROR")
    client = DummyClient(DummyResponse(status_code=200), raise_exc=True)
    ok = await telegram.send_message("timeout", client=client, rule="roi")
    assert ok is False
    assert "telegram.exception" in caplog.text
    assert failed_counter.records[0]["error_type"] == "exception"
    assert not sent_counter.records
