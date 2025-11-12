from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from typing import Any, Literal

import httpx
import structlog

from awa_common.metrics import (
    ALERTBOT_INFLIGHT_SENDS,
    ALERTBOT_MESSAGES_SENT_TOTAL,
    ALERTBOT_SEND_LATENCY_SECONDS,
    ALERTBOT_TELEGRAM_ERRORS_TOTAL,
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

    try:
        payload = response.json()
    except ValueError:
        _LOGGER.error(
            "telegram.invalid_json",
            method=method,
            status_code=response.status_code,
            body=response.text[:512],
        )
        _record_failure(rule, "invalid_response")
        return False

    if not payload.get("ok", False):
        description = payload.get("description") or payload.get("error_code") or "unknown error"
        _LOGGER.error(
            "telegram.api_error",
            method=method,
            status_code=response.status_code,
            description=description,
        )
        _record_failure(rule, "api_error")
        return False

    _record_success(rule)
    return True


@dataclass(slots=True)
class TelegramResponse:
    ok: bool
    status_code: int
    payload: dict[str, Any] | None
    description: str | None = None
    error_code: int | None = None
    retry_after: float | None = None


@dataclass(slots=True)
class TelegramSendResult:
    ok: bool
    status: Literal["ok", "retry", "error"]
    response: TelegramResponse | None = None

    @property
    def description(self) -> str | None:
        return self.response.description if self.response else None

    @property
    def error_code(self) -> int | None:
        return self.response.error_code if self.response else None

    @property
    def retry_after(self) -> float | None:
        return self.response.retry_after if self.response else None


class _TokenBucket:
    """Minimal asyncio-friendly token bucket."""

    def __init__(self, rate: float, *, burst: float | None = None) -> None:
        self.rate = max(float(rate), 0.0)
        capacity = burst if burst and burst > 0 else max(self.rate * 2, 1.0)
        self.capacity = capacity if self.rate > 0 else 0.0
        self.tokens = self.capacity
        self.updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        if self.rate <= 0:
            return
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = max(0.0, now - self.updated)
                if elapsed:
                    self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                    self.updated = now
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                deficit = 1.0 - self.tokens
                wait_time = deficit / self.rate if self.rate > 0 else 0.01
            await asyncio.sleep(min(max(wait_time, 0.05), 1.0))


def _metric_base_labels() -> dict[str, str]:
    service = (settings.SERVICE_NAME or "api").strip() or "api"
    env = (settings.ENV or "local").strip() or "local"
    version = (settings.VERSION or "0.0.0").strip() or "0.0.0"
    return {"service": service, "env": env, "version": version}


def _retry_after_from_payload(payload: dict[str, Any]) -> float | None:
    parameters = payload.get("parameters")
    if isinstance(parameters, dict):
        retry_after = parameters.get("retry_after")
        if isinstance(retry_after, (int, float)) and retry_after >= 0:
            return float(retry_after)
    return None


class AsyncTelegramClient:
    """Async Telegram client with concurrency, throttling, and structured results."""

    def __init__(
        self,
        *,
        token: str | None = None,
        base_url: str | None = None,
        max_concurrency: int | None = None,
        max_rps: float | None = None,
        max_chat_rps: float | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._token = (token or settings.TELEGRAM_TOKEN or "").strip()
        self._base_url = (base_url or settings.TELEGRAM_API_BASE or "https://api.telegram.org").rstrip("/")
        timeout = httpx.Timeout(settings.TELEGRAM_TOTAL_TIMEOUT_S, connect=settings.TELEGRAM_CONNECT_TIMEOUT_S)
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._owns_client = client is None
        self._max_concurrency = max_concurrency if max_concurrency is not None else settings.ALERT_SEND_CONCURRENCY
        self._send_semaphore = None
        if self._max_concurrency and self._max_concurrency > 0:
            self._send_semaphore = asyncio.Semaphore(self._max_concurrency)
        self._global_bucket = None
        global_rps = max_rps if max_rps is not None else settings.ALERT_TELEGRAM_MAX_RPS
        if global_rps and global_rps > 0:
            self._global_bucket = _TokenBucket(global_rps)
        per_chat_rps = max_chat_rps if max_chat_rps is not None else settings.ALERT_TELEGRAM_MAX_CHAT_RPS
        self._per_chat_rate = per_chat_rps if per_chat_rps and per_chat_rps > 0 else None
        self._chat_buckets: dict[str, _TokenBucket] = {}
        self._chat_bucket_lock = asyncio.Lock()
        self._metric_labels = _metric_base_labels()
        self._logger = structlog.get_logger(__name__).bind(
            service=self._metric_labels["service"],
            env=self._metric_labels["env"],
            version=self._metric_labels["version"],
            component="telegram_client",
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        *,
        parse_mode: str | None = "HTML",
        disable_web_page_preview: bool = True,
        disable_notification: bool | None = None,
        rule_id: str | None = None,
    ) -> TelegramSendResult:
        normalized_chat_id, problem = self._coerce_chat_id(chat_id)
        if normalized_chat_id is None:
            response = TelegramResponse(
                ok=False,
                status_code=0,
                payload=None,
                description=problem or "chat_id missing",
                error_code=None,
            )
            result = TelegramSendResult(ok=False, status="error", response=response)
            self._record_result(result, rule_id=rule_id, chat_id=str(chat_id), method="sendMessage")
            return result
        payload: dict[str, Any] = {"chat_id": normalized_chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if disable_web_page_preview is not None:
            payload["disable_web_page_preview"] = disable_web_page_preview
        if disable_notification is not None:
            payload["disable_notification"] = disable_notification
        return await self._send(
            method="sendMessage",
            payload=payload,
            chat_key=str(normalized_chat_id),
            chat_display=str(normalized_chat_id),
            rule_id=rule_id,
        )

    async def get_me(self) -> TelegramResponse:
        return await self._request("getMe", payload={})

    async def get_chat(self, chat_id: int | str) -> TelegramResponse:
        normalized_chat_id, _ = self._coerce_chat_id(chat_id)
        payload: dict[str, Any] = {"chat_id": normalized_chat_id if normalized_chat_id is not None else chat_id}
        return await self._request("getChat", payload=payload)

    async def _send(
        self,
        *,
        method: str,
        payload: dict[str, Any],
        chat_key: str,
        chat_display: str,
        rule_id: str | None,
    ) -> TelegramSendResult:
        if not self._token:
            response = TelegramResponse(
                ok=False,
                status_code=0,
                payload=None,
                description="TELEGRAM_TOKEN missing",
            )
            result = TelegramSendResult(ok=False, status="error", response=response)
            self._record_result(result, rule_id=rule_id, chat_id=chat_display, method=method)
            return result
        semaphore = self._send_semaphore
        if semaphore is not None:
            await semaphore.acquire()
        try:
            await self._rate_limit(chat_key)
            inflight_labels = dict(self._metric_labels)
            ALERTBOT_INFLIGHT_SENDS.labels(**inflight_labels).inc()
            start = time.perf_counter()
            try:
                response = await self._request(method, payload)
            finally:
                ALERTBOT_SEND_LATENCY_SECONDS.labels(**inflight_labels).observe(time.perf_counter() - start)
                ALERTBOT_INFLIGHT_SENDS.labels(**inflight_labels).dec()
        finally:
            if semaphore is not None:
                semaphore.release()
        status: Literal["ok", "retry", "error"]
        if response.ok:
            status = "ok"
        elif response.retry_after is not None or response.status_code == 429:
            status = "retry"
        else:
            status = "error"
        result = TelegramSendResult(ok=response.ok, status=status, response=response)
        self._record_result(result, rule_id=rule_id, chat_id=chat_display, method=method)
        return result

    async def _rate_limit(self, chat_key: str) -> None:
        if self._global_bucket is not None:
            await self._global_bucket.acquire()
        if self._per_chat_rate is None:
            return
        bucket = await self._get_or_create_chat_bucket(chat_key)
        await bucket.acquire()

    async def _get_or_create_chat_bucket(self, chat_key: str) -> _TokenBucket:
        async with self._chat_bucket_lock:
            bucket = self._chat_buckets.get(chat_key)
            if bucket is None:
                bucket = _TokenBucket(self._per_chat_rate or 0.0)
                self._chat_buckets[chat_key] = bucket
            return bucket

    async def _request(self, method: str, payload: dict[str, Any]) -> TelegramResponse:
        url = f"{self._base_url}/bot{self._token}/{method}"
        try:
            response = await self._client.post(url, json=payload)
        except httpx.RequestError as exc:
            description = f"{exc.__class__.__name__}: {exc}"
            return TelegramResponse(ok=False, status_code=0, payload=None, description=description)
        data: dict[str, Any] | None = None
        try:
            data_candidate = response.json()
            if isinstance(data_candidate, dict):
                data = data_candidate
        except ValueError:
            data = None
        if response.status_code >= 400:
            description = data.get("description") if data else response.text[:256]
            error_code = data.get("error_code") if data else response.status_code
            retry_after = _retry_after_from_payload(data) if data else None
            return TelegramResponse(
                ok=False,
                status_code=response.status_code,
                payload=data,
                description=description,
                error_code=error_code,
                retry_after=retry_after,
            )
        if data is None:
            return TelegramResponse(ok=True, status_code=response.status_code, payload=None)
        retry_after = _retry_after_from_payload(data)
        description = data.get("description")
        error_code = data.get("error_code")
        ok = bool(data.get("ok", True))
        return TelegramResponse(
            ok=ok,
            status_code=response.status_code,
            payload=data,
            description=description,
            error_code=error_code,
            retry_after=retry_after,
        )

    def _record_result(self, result: TelegramSendResult, *, rule_id: str | None, chat_id: str, method: str) -> None:
        labels = dict(self._metric_labels)
        rule_label = (rule_id or "global").strip() or "global"
        ALERTBOT_MESSAGES_SENT_TOTAL.labels(rule=rule_label, status=result.status, **labels).inc()
        if not result.ok:
            error_code = result.error_code or (result.response.status_code if result.response else "unknown")
            ALERTBOT_TELEGRAM_ERRORS_TOTAL.labels(error_code=str(error_code), **labels).inc()
            self._logger.warning(
                "telegram.send_failed",
                rule_id=rule_id,
                chat_id=chat_id,
                method=method,
                status=result.status,
                error_code=error_code,
                description=result.description,
                retry_after=result.retry_after,
            )
        else:
            self._logger.debug("telegram.send_ok", rule_id=rule_id, chat_id=chat_id, method=method)

    def _coerce_chat_id(self, chat_id: int | str | None) -> tuple[int | str | None, str | None]:
        if chat_id is None:
            return None, "chat_id missing"
        if isinstance(chat_id, int):
            return chat_id, None
        text = str(chat_id).strip()
        if not text:
            return None, "chat_id missing"
        numeric = text.lstrip("-")
        if numeric.isdigit():
            try:
                return int(text), None
            except ValueError:
                pass
        return text, None


__all__ = [
    "validate_config",
    "send_message",
    "send_photo",
    "send_document",
    "AsyncTelegramClient",
    "TelegramSendResult",
    "TelegramResponse",
]
