from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx
import structlog

from awa_common.metrics import (
    ALERTS_NOTIFICATIONS_FAILED_TOTAL,
    ALERTS_NOTIFICATIONS_SENT_TOTAL,
)
from awa_common.settings import settings

_TOKEN_PATTERN = re.compile(r"^\d{5,}:[A-Za-z0-9_-]{10,}$")
_ASYNC_CLIENT: httpx.AsyncClient | None = None
_ASYNC_CLIENT_LOCK = asyncio.Lock()
_CHANNEL = "telegram"
_LOGGER = structlog.get_logger(__name__).bind(
    service=(settings.SERVICE_NAME or "api"),
    env=settings.ENV,
    version=settings.VERSION,
    component="telegram",
)


def _base_labels(rule: str | None) -> dict[str, str]:
    resolved_rule = (rule or "global").strip() or "global"
    return {
        "rule": resolved_rule,
        "channel": _CHANNEL,
        "service": (settings.SERVICE_NAME or "api"),
        "env": settings.ENV,
        "version": settings.VERSION,
    }


def _record_success(rule: str | None) -> None:
    ALERTS_NOTIFICATIONS_SENT_TOTAL.labels(**_base_labels(rule)).inc()


def _record_failure(rule: str | None, error_type: str) -> None:
    ALERTS_NOTIFICATIONS_FAILED_TOTAL.labels(**{**_base_labels(rule), "error_type": error_type}).inc()


async def _ensure_async_client() -> httpx.AsyncClient:
    global _ASYNC_CLIENT
    client = _ASYNC_CLIENT
    if client is not None:
        return client
    async with _ASYNC_CLIENT_LOCK:
        if _ASYNC_CLIENT is None:
            timeout = httpx.Timeout(settings.TELEGRAM_TOTAL_TIMEOUT_S, connect=settings.TELEGRAM_CONNECT_TIMEOUT_S)
            _ASYNC_CLIENT = httpx.AsyncClient(timeout=timeout)
        return _ASYNC_CLIENT


def _normalize_chat_id(chat_id: int | str | None) -> tuple[int | None, str | None]:
    if chat_id is None:
        return None, "chat_id missing"
    if isinstance(chat_id, int):
        return chat_id, None
    text = str(chat_id).strip()
    if not text:
        return None, "chat_id missing"
    try:
        return int(text), None
    except ValueError:
        return None, "chat_id must be an integer"


def validate_config(
    token: str | None,
    chat_id: int | str | None,
    client: httpx.Client | None = None,
) -> tuple[bool, str]:
    """Validate Telegram configuration by checking formats and performing a lightweight API call."""

    trimmed_token = (token or "").strip()
    if not trimmed_token:
        return False, "TELEGRAM_TOKEN missing"
    if not _TOKEN_PATTERN.match(trimmed_token):
        return False, "TELEGRAM_TOKEN format is invalid"

    normalized_chat_id, reason = _normalize_chat_id(chat_id)
    if normalized_chat_id is None:
        return False, reason or "TELEGRAM_DEFAULT_CHAT_ID invalid"

    http_client = client
    close_client = False
    if http_client is None:
        timeout = httpx.Timeout(settings.TELEGRAM_TOTAL_TIMEOUT_S, connect=settings.TELEGRAM_CONNECT_TIMEOUT_S)
        http_client = httpx.Client(timeout=timeout)
        close_client = True
    try:
        url = f"https://api.telegram.org/bot{trimmed_token}/getMe"
        response = http_client.get(url)
    except httpx.RequestError as exc:
        return False, f"telegram API error: {exc.__class__.__name__}: {exc}"
    finally:
        if close_client:
            http_client.close()

    if response.status_code >= 400:
        return False, f"telegram API rejected token: HTTP {response.status_code}"
    try:
        payload = response.json()
    except ValueError:
        return False, "telegram API returned invalid JSON"
    if not payload.get("ok", False):
        description = payload.get("description") or "unknown error"
        return False, f"telegram API error: {description}"
    profile = payload.get("result") or {}
    username = profile.get("username") or profile.get("first_name") or ""
    return True, f"connected as @{username}" if username else "configuration valid"


async def send_message(
    text: str,
    chat_id: int | str | None = None,
    parse_mode: str = "HTML",
    disable_notification: bool | None = None,
    client: httpx.AsyncClient | None = None,
    *,
    rule: str | None = None,
) -> bool:
    """Send a Telegram text message."""

    payload = {"text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return await _send_payload(
        method="sendMessage",
        payload=payload,
        chat_id_override=chat_id,
        disable_notification=disable_notification,
        client=client,
        rule=rule,
    )


async def send_photo(
    photo: str,
    caption: str | None = None,
    chat_id: int | str | None = None,
    parse_mode: str = "HTML",
    disable_notification: bool | None = None,
    client: httpx.AsyncClient | None = None,
    *,
    rule: str | None = None,
) -> bool:
    """Send a Telegram photo attachment with optional caption."""

    payload: dict[str, Any] = {"photo": photo}
    if caption:
        payload["caption"] = caption
    if caption and parse_mode:
        payload["parse_mode"] = parse_mode
    return await _send_payload(
        method="sendPhoto",
        payload=payload,
        chat_id_override=chat_id,
        disable_notification=disable_notification,
        client=client,
        rule=rule,
    )


async def send_document(
    document: str,
    caption: str | None = None,
    chat_id: int | str | None = None,
    parse_mode: str = "HTML",
    disable_notification: bool | None = None,
    client: httpx.AsyncClient | None = None,
    *,
    rule: str | None = None,
) -> bool:
    """Send a Telegram document attachment with optional caption."""

    payload: dict[str, Any] = {"document": document}
    if caption:
        payload["caption"] = caption
    if caption and parse_mode:
        payload["parse_mode"] = parse_mode
    return await _send_payload(
        method="sendDocument",
        payload=payload,
        chat_id_override=chat_id,
        disable_notification=disable_notification,
        client=client,
        rule=rule,
    )


async def _send_payload(
    method: str,
    payload: dict[str, Any],
    *,
    chat_id_override: int | str | None,
    disable_notification: bool | None,
    client: httpx.AsyncClient | None,
    rule: str | None,
) -> bool:
    token = (settings.TELEGRAM_TOKEN or "").strip()
    if not token:
        _LOGGER.warning("telegram.disabled", reason="missing token")
        _record_failure(rule, "disabled")
        return False

    target_chat_id = chat_id_override if chat_id_override is not None else settings.TELEGRAM_DEFAULT_CHAT_ID
    normalized_chat_id, reason = _normalize_chat_id(target_chat_id)
    if normalized_chat_id is None:
        _LOGGER.warning("telegram.disabled", reason=reason or "invalid chat_id")
        _record_failure(rule, "disabled")
        return False

    payload = {**payload, "chat_id": normalized_chat_id}
    if disable_notification is not None:
        payload["disable_notification"] = disable_notification

    http_client = client or await _ensure_async_client()
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        response = await http_client.post(url, json=payload)
    except httpx.RequestError as exc:
        _LOGGER.error(
            "telegram.exception",
            method=method,
            error=str(exc),
            error_type=exc.__class__.__name__,
        )
        _record_failure(rule, "exception")
        return False

    if response.status_code >= 400:
        truncated_body = response.text[:512]
        _LOGGER.error(
            "telegram.http_error",
            method=method,
            status_code=response.status_code,
            body=truncated_body,
        )
        _record_failure(rule, "http_error")
        return False

    _record_success(rule)
    return True


__all__ = ["validate_config", "send_message", "send_photo", "send_document"]
