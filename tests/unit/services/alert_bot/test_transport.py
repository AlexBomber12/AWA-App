from __future__ import annotations

import pytest

from awa_common import telegram
from awa_common.metrics import ALERT_ERRORS_TOTAL, ALERTS_SENT_TOTAL
from services.alert_bot.decider import AlertRequest
from services.alert_bot.transport import TelegramTransport


class StubAsyncClient:
    def __init__(self, results: list[telegram.TelegramSendResult], *, chat_ok: bool = True) -> None:
        self._results = results
        self.calls: list[tuple[str, str]] = []
        self.chat_ok = chat_ok

    async def send_message(self, *, chat_id: int | str, text: str, **_: object) -> telegram.TelegramSendResult:
        self.calls.append((str(chat_id), text))
        return self._results.pop(0)

    async def get_me(self) -> telegram.TelegramResponse:
        return telegram.TelegramResponse(ok=True, status_code=200, payload={})  # type: ignore[attr-defined]

    async def get_chat(self, chat_id: int | str) -> telegram.TelegramResponse:
        if self.chat_ok:
            return telegram.TelegramResponse(ok=True, status_code=200, payload={"id": chat_id})  # type: ignore[attr-defined]
        return telegram.TelegramResponse(ok=False, status_code=403, payload={}, description="forbidden")  # type: ignore[attr-defined]


def _intent() -> AlertRequest:
    return AlertRequest(
        rule_id="roi",
        severity="critical",
        chat_id="123",
        message="alert",
        parse_mode="HTML",
        dedupe_key="roi:1",
        disable_web_page_preview=True,
    )


@pytest.mark.asyncio
async def test_transport_records_success_metrics() -> None:
    result = telegram.TelegramSendResult(ok=True, status="ok", response=None)  # type: ignore[attr-defined]
    client = StubAsyncClient([result])
    labels = {"service": "test", "env": "test", "version": "test"}
    transport = TelegramTransport(client=client, metric_labels=labels)
    intent = _intent()
    metric = ALERTS_SENT_TOTAL.labels(
        rule=intent.rule_id,
        severity=intent.severity,
        channel="telegram",
        status="success",
        **labels,
    )
    before = metric._value.get()
    await transport.send(intent)
    assert metric._value.get() == before + 1


@pytest.mark.asyncio
async def test_transport_records_failure_metrics() -> None:
    response = telegram.TelegramResponse(  # type: ignore[attr-defined]
        ok=False,
        status_code=500,
        payload={"description": "boom"},
        description="boom",
        error_code=500,
        retry_after=None,
    )
    result = telegram.TelegramSendResult(ok=False, status="error", response=response)  # type: ignore[attr-defined]
    client = StubAsyncClient([result])
    labels = {"service": "test", "env": "test", "version": "test"}
    transport = TelegramTransport(client=client, metric_labels=labels)
    intent = _intent()
    sent_metric = ALERTS_SENT_TOTAL.labels(
        rule=intent.rule_id,
        severity=intent.severity,
        channel="telegram",
        status="failed",
        **labels,
    )
    error_metric = ALERT_ERRORS_TOTAL.labels(rule=intent.rule_id, type="HTTP_5xx", **labels)
    before_sent = sent_metric._value.get()
    before_err = error_metric._value.get()
    await transport.send(intent)
    assert sent_metric._value.get() == before_sent + 1
    assert error_metric._value.get() == before_err + 1


@pytest.mark.asyncio
async def test_transport_validation_reports_chat_errors() -> None:
    client = StubAsyncClient([], chat_ok=False)
    transport = TelegramTransport(client=client, metric_labels={})
    ok, reason = await transport.validate({"123"})
    assert not ok
    assert reason and reason.startswith("chat_invalid")
