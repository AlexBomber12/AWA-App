from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from awa_common.cron_config import validate_cron_expr
from awa_common.settings import settings as global_settings

_TOKEN_PATTERN = re.compile(r"^\d{5,}:[A-Za-z0-9_-]{10,}$")
_PLACEHOLDER_MARKERS = ("changeme", "placeholder", "example")


class AlertBotSettings(BaseModel):
    """Typed configuration extracted from the shared settings object."""

    enabled: bool = True
    telegram_token: str = ""
    default_chat_id: str | None = None
    evaluation_cron: str = Field(default="*/5 * * * *", description="Primary schedule for alertbot.run")
    send_cron: str = Field(default="*/1 * * * *", description="Alias used by Celery beat")
    eval_concurrency: int = 8
    send_concurrency: int = 8
    rule_timeout_s: float = 15.0
    env: str = "local"
    service_name: str = "alert_bot"
    version: str = "0.0.0"

    @field_validator("telegram_token", mode="before")
    @classmethod
    def _trim_token(cls, value: str | None) -> str:
        return (value or "").strip()

    @field_validator("default_chat_id", mode="before")
    @classmethod
    def _normalize_chat(cls, value: str | int | None) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("evaluation_cron", "send_cron", mode="before")
    @classmethod
    def _validate_cron(cls, value: str, info: ValidationInfo) -> str:
        expression = (value or "").strip()
        validate_cron_expr(expression, source=info.field_name)
        return expression

    @classmethod
    def load(cls) -> AlertBotSettings:
        shared = global_settings
        return cls(
            enabled=bool(shared.ALERTS_ENABLED),
            telegram_token=shared.TELEGRAM_TOKEN,
            default_chat_id=cls._normalize_chat(shared.TELEGRAM_DEFAULT_CHAT_ID),
            evaluation_cron=shared.ALERTS_EVALUATION_INTERVAL_CRON,
            send_cron=shared.ALERT_SCHEDULE_CRON,
            eval_concurrency=int(shared.ALERT_EVAL_CONCURRENCY),
            send_concurrency=int(shared.ALERT_SEND_CONCURRENCY),
            rule_timeout_s=float(shared.ALERT_RULE_TIMEOUT_S),
            env=shared.ENV,
            service_name=(shared.SERVICE_NAME or "alert_bot") or "alert_bot",
            version=shared.VERSION,
        )

    def base_metric_labels(self) -> dict[str, str]:
        return {
            "service": (self.service_name or "alert_bot") or "alert_bot",
            "env": (self.env or "local") or "local",
            "version": self.version or "0.0.0",
        }

    def validate_runtime(self) -> tuple[bool, str | None]:
        """Return (ok, reason) indicating whether Telegram config looks sane."""

        token = (self.telegram_token or "").strip()
        if not token:
            return False, "TELEGRAM_TOKEN missing"
        lowered = token.lower()
        if any(marker in lowered for marker in _PLACEHOLDER_MARKERS):
            return False, "TELEGRAM_TOKEN placeholder"
        if not _TOKEN_PATTERN.match(token):
            return False, "TELEGRAM_TOKEN format invalid"
        chat = (self.default_chat_id or "").strip()
        if not chat:
            return False, "TELEGRAM_DEFAULT_CHAT_ID missing"
        if chat.lower() in {"changeme", "placeholder", "example"}:
            return False, "TELEGRAM_DEFAULT_CHAT_ID placeholder"
        return True, None


@dataclass(slots=True)
class TelegramValidationResult:
    ok: bool
    reason: str | None = None


__all__ = ["AlertBotSettings", "TelegramValidationResult"]
