from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import httpx
import structlog

from awa_common.http_client import AsyncHTTPClient, HTTPClientError
from awa_common.llm import LLMConfigurationError
from awa_common.metrics import (
    observe_llm_provider_latency,
    record_llm_provider_request,
    record_llm_provider_timeout,
)

from .errors import (
    LLMProviderClientError,
    LLMProviderError,
    LLMProviderServerError,
    LLMProviderTimeoutError,
    LLMProviderTransportError,
)

logger = structlog.get_logger(__name__).bind(component="llm_provider_client")

ProviderOutcome = str


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    base_url: str
    api_key: str | None
    integration: str


class LLMProviderHTTPClient:
    """Async client for OpenAI-compatible providers with retries, metrics, and error mapping."""

    def __init__(
        self,
        *,
        config: ProviderConfig,
        request_timeout_s: float,
        max_retries: int,
        backoff_base_s: float,
        backoff_max_s: float,
        retry_status_codes: Iterable[int] | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not config.base_url:
            raise LLMConfigurationError("LLM provider base URL is required")
        self._config = ProviderConfig(
            name=(config.name or "unknown"),
            base_url=(config.base_url or "").rstrip("/"),
            api_key=(config.api_key or None),
            integration=(config.integration or "llm_provider"),
        )
        self._request_timeout_s = float(request_timeout_s)
        self._max_retries = max(1, int(max_retries))
        self._backoff_base_s = float(backoff_base_s)
        self._backoff_max_s = float(backoff_max_s)
        self._retry_status_codes = tuple(int(code) for code in retry_status_codes) if retry_status_codes else None
        self._transport = transport

    @property
    def provider(self) -> str:
        return self._config.name

    def _headers(self) -> dict[str, str]:
        if not self._config.api_key:
            return {}
        return {"Authorization": f"Bearer {self._config.api_key}"}

    def _classify_exception(self, exc: BaseException) -> ProviderOutcome:
        if isinstance(exc, LLMProviderTimeoutError):
            return "timeout"
        if isinstance(exc, LLMProviderClientError):
            return "client_error"
        if isinstance(exc, LLMProviderServerError):
            return "server_error"
        if isinstance(exc, LLMProviderTransportError):
            return "transport_error"
        if isinstance(exc, LLMProviderError):
            return "error"
        if isinstance(exc, httpx.TimeoutException):
            return "timeout"
        if isinstance(exc, HTTPClientError):
            original = getattr(exc, "original", None)
            if isinstance(original, BaseException):
                return self._classify_exception(original)
            return "retry_exhausted"
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code if exc.response is not None else None
            if status and 400 <= status < 500:
                return "client_error"
            if status and status >= 500:
                return "server_error"
            return "error"
        if isinstance(exc, httpx.RequestError):
            return "transport_error"
        return "error"

    def _convert_exception(self, exc: BaseException, outcome: ProviderOutcome) -> LLMProviderError:
        status: int | None = None
        if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
            status = exc.response.status_code
        if outcome == "timeout":
            return LLMProviderTimeoutError(provider=self.provider)
        if outcome == "client_error":
            return LLMProviderClientError(provider=self.provider, status=status)
        if outcome == "server_error":
            return LLMProviderServerError(provider=self.provider, status=status)
        if outcome == "transport_error":
            return LLMProviderTransportError(provider=self.provider)
        if outcome == "retry_exhausted":
            return LLMProviderServerError("LLM provider retry budget exhausted", provider=self.provider, status=status)
        return LLMProviderServerError(provider=self.provider, status=status)

    def _log_failure(self, exc: BaseException, outcome: ProviderOutcome, operation: str) -> None:
        status = None
        if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
            status = exc.response.status_code
        logger.warning(
            "llm.provider.http_failure",
            provider=self.provider,
            integration=self._config.integration,
            operation=operation,
            outcome=outcome,
            status_code=status,
            error_type=exc.__class__.__name__,
            error=str(exc),
        )

    async def chat_completion(self, payload: dict[str, Any], *, operation: str = "chat_completion") -> Any:
        base = self._config.base_url.rstrip("/")
        if base.endswith("/v1"):
            url = f"{base}/chat/completions"
        else:
            url = f"{base}/v1/chat/completions"
        start = time.perf_counter()
        outcome: ProviderOutcome = "error"
        try:
            async with AsyncHTTPClient(
                integration=self._config.integration,
                total_timeout_s=self._request_timeout_s,
                max_retries=self._max_retries,
                backoff_base_s=self._backoff_base_s,
                backoff_max_s=self._backoff_max_s,
                retry_status_codes=self._retry_status_codes,
                transport=self._transport,
            ) as client:
                response_json = await client.post_json(
                    url,
                    json=payload,
                    headers=self._headers(),
                    timeout=self._request_timeout_s,
                )
            outcome = "success"
            return response_json
        except Exception as exc:
            outcome = self._classify_exception(exc)
            self._log_failure(exc, outcome, operation)
            raise self._convert_exception(exc, outcome) from exc
        finally:
            duration = time.perf_counter() - start
            record_llm_provider_request(self.provider, operation, outcome)
            observe_llm_provider_latency(self.provider, operation, duration)
            if outcome == "timeout":
                record_llm_provider_timeout(self.provider, operation)
