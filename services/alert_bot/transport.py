from __future__ import annotations

import structlog

from awa_common.metrics import ALERT_ERRORS_TOTAL, ALERTS_SENT_TOTAL
from awa_common.telegram import AsyncTelegramClient, TelegramResponse, TelegramSendResult
from services.alert_bot.decider import NotificationIntent


class TelegramTransport:
    """Transport layer responsible for delivering intents to Telegram."""

    def __init__(
        self,
        *,
        client: AsyncTelegramClient | None = None,
        metric_labels: dict[str, str] | None = None,
    ) -> None:
        self._client = client or AsyncTelegramClient()
        self._metric_labels = metric_labels or {}
        self._logger = structlog.get_logger(__name__).bind(component="alertbot_transport", **self._metric_labels)

    async def validate(self, chat_ids: set[str]) -> tuple[bool, str | None]:
        token_status = await self._client.get_me()
        if not token_status.ok:
            description = token_status.description or "invalid_token"
            self._logger.error("telegram.validation.failed", error=description)
            return False, description
        for chat_id in chat_ids:
            chat_status = await self._client.get_chat(chat_id)
            if not chat_status.ok:
                description = chat_status.description or "unknown_error"
                self._logger.error("telegram.validation.chat_failed", chat_id=chat_id, error=description)
                return False, f"chat_invalid:{chat_id}"
        self._logger.info("telegram.validation.success", chats=len(chat_ids))
        return True, None

    async def send(self, chat_id: str, intent: NotificationIntent) -> TelegramSendResult:
        result = await self._client.send_message(
            chat_id=chat_id,
            text=intent.message,
            parse_mode=intent.parse_mode,
            disable_web_page_preview=intent.disable_web_page_preview,
            rule_id=intent.rule_id,
        )
        self._record_metrics(intent, result, chat_id)
        return result

    def _record_metrics(self, intent: NotificationIntent, result: TelegramSendResult, chat_id: str) -> None:
        status_label = "success" if result.ok else "failed"
        ALERTS_SENT_TOTAL.labels(
            rule=intent.rule_id,
            severity=intent.severity,
            channel="telegram",
            status=status_label,
            **self._metric_labels,
        ).inc()
        if result.ok:
            self._logger.debug("telegram.send_ok", rule=intent.rule_id, chat_id=chat_id)
            return
        error_type = _classify_error(result)
        ALERT_ERRORS_TOTAL.labels(rule=intent.rule_id, type=error_type, **self._metric_labels).inc()
        self._logger.warning(
            "telegram.send_failed",
            rule=intent.rule_id,
            chat_id=chat_id,
            status=result.status,
            error_type=error_type,
            description=result.description,
            retry_after=result.retry_after,
        )


def _classify_error(result: TelegramSendResult) -> str:
    response: TelegramResponse | None = result.response
    if result.status == "retry":
        return "telegram_api_error"
    if response is not None and response.status_code >= 500:
        return "http_error"
    if response is not None and response.status_code in {401, 403}:
        return "config_error"
    return "telegram_api_error"


__all__ = ["TelegramTransport"]
