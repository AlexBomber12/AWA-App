from __future__ import annotations

import contextlib
import inspect
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx
import structlog
from structlog import contextvars as structlog_contextvars
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    RetryError,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    stop_after_delay,
    wait_random_exponential,
)

from awa_common.metrics import (
    observe_external_http_latency,
    record_external_http_request,
    record_external_http_retry,
)
from awa_common.settings import settings

__all__ = ["AsyncHTTPClient", "HTTPClient", "HTTPClientError", "RetryableStatusError"]

logger = structlog.get_logger(__name__)


class HTTPClientError(Exception):
    """Raised when an HTTP request fails after exhausting all retries."""

    def __init__(self, message: str, *, original: Exception | None = None) -> None:
        super().__init__(message)
        self.original = original


class RetryableStatusError(httpx.HTTPStatusError):
    """Internal exception used to trigger retries for retryable HTTP responses."""

    def __init__(
        self,
        message: str,
        *,
        request: httpx.Request,
        response: httpx.Response,
        retry_after: float | None,
    ) -> None:
        super().__init__(message, request=request, response=response)
        self.retry_after = retry_after


def _default_timeout() -> httpx.Timeout:
    return httpx.Timeout(
        timeout=settings.HTTP_TOTAL_TIMEOUT_S,
        connect=settings.HTTP_CONNECT_TIMEOUT_S,
        read=settings.HTTP_READ_TIMEOUT_S,
        write=settings.HTTP_READ_TIMEOUT_S,
        pool=settings.HTTP_POOL_TIMEOUT_S,
    )


def _default_limits() -> httpx.Limits:
    return httpx.Limits(
        max_connections=settings.HTTP_MAX_CONNECTIONS,
        max_keepalive_connections=settings.HTTP_MAX_KEEPALIVE_CONNECTIONS,
    )


def _safe_url(url: str) -> str:
    parsed = urlparse(url)
    safe = parsed._replace(query="", params="", fragment="")
    return urlunparse(safe)


def _classify_exception(exc: BaseException) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, RetryError):
        return "retry_exhausted"
    return "error"


def _retryable_exceptions() -> tuple[type[Exception], ...]:
    return (httpx.RequestError, RetryableStatusError)


def _is_retryable_exception(exc: BaseException | None) -> bool:
    return isinstance(exc, _retryable_exceptions())


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.isdigit():
        try:
            parsed = float(text)
        except ValueError:
            return None
        return max(0.0, parsed)
    with contextlib.suppress(ValueError, TypeError):
        from datetime import UTC, datetime
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(text)
        if not dt:
            return None
        now = datetime.now(UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return max(0.0, (dt - now).total_seconds())
    return None


def _retry_reason(exc: BaseException | None) -> tuple[str, int | None]:
    if exc is None:
        return "success", None
    if isinstance(exc, RetryableStatusError) and exc.response is not None:
        return str(exc.response.status_code), exc.response.status_code
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return str(exc.response.status_code), exc.response.status_code
    if isinstance(exc, httpx.TimeoutException):
        return "timeout", None
    return exc.__class__.__name__, None


def _convert_retry_exception(exc: BaseException | None, *, url: str) -> Exception:
    if isinstance(exc, RetryableStatusError):
        return httpx.HTTPStatusError(str(exc), request=exc.request, response=exc.response)
    if isinstance(exc, Exception):
        return exc
    return HTTPClientError(f"HTTP request to {url} failed", original=exc if isinstance(exc, Exception) else None)


class _RetryWait(wait_random_exponential):
    def __init__(self, *, jitter: float, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._jitter = max(0.0, jitter)

    def __call__(self, retry_state: RetryCallState) -> float:
        retry_after: float | None = None
        if retry_state.outcome is not None:
            if retry_state.outcome.failed:
                exc = retry_state.outcome.exception()
                retry_after = getattr(exc, "retry_after", None)
            else:
                result = retry_state.outcome.result()
                if isinstance(result, httpx.Response):
                    retry_after = _parse_retry_after(result.headers.get("Retry-After"))
        if retry_after is not None:
            return min(float(retry_after), float(self.max or retry_after))
        delay = super().__call__(retry_state)
        if self._jitter > 0:
            import random

            delay += random.uniform(0.0, self._jitter)
        return delay


@dataclass
class _RequestLog:
    integration: str
    method: str
    url: str
    task_id: str | None
    request_id: str | None

    def __post_init__(self) -> None:
        self._logger = logger.bind(
            integration=self.integration,
            method=self.method,
        )
        self._safe_url = _safe_url(self.url)
        self._start = time.perf_counter()
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._logger.debug(
            "external_http.request.start",
            url=self._safe_url,
            task_id=self.task_id,
            request_id=self.request_id,
        )

    def success(self, status_code: int, attempts: int) -> None:
        duration = time.perf_counter() - self._start
        self._logger.info(
            "external_http.request.success",
            url=self._safe_url,
            status_code=status_code,
            attempts=attempts,
            duration_ms=int(duration * 1000),
            task_id=self.task_id,
            request_id=self.request_id,
        )

    def failure(self, exc: BaseException, attempts: int) -> None:
        duration = time.perf_counter() - self._start
        status_code = None
        if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
            status_code = exc.response.status_code
        self._logger.warning(
            "external_http.request.failure",
            url=self._safe_url,
            error=str(exc),
            error_type=exc.__class__.__name__,
            status_code=status_code,
            attempts=attempts,
            duration_ms=int(duration * 1000),
            task_id=self.task_id,
            request_id=self.request_id,
        )


class _BaseHTTPClient:
    def __init__(
        self,
        *,
        integration: str,
        timeout: httpx.Timeout | None = None,
        limits: httpx.Limits | None = None,
        headers: dict[str, str] | None = None,
        base_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
        max_retries: int | None = None,
        total_timeout_s: float | None = None,
        backoff_base_s: float | None = None,
        backoff_max_s: float | None = None,
        retry_jitter_s: float | None = None,
        retry_status_codes: tuple[int, ...] | list[int] | set[int] | frozenset[int] | None = None,
    ) -> None:
        self.integration = (integration or "default").strip().lower() or "default"
        self._timeout = timeout or _default_timeout()
        self._limits = limits or _default_limits()
        self._headers = headers
        self._base_url = base_url
        self._transport = transport
        self._max_retries = max(1, int(max_retries if max_retries is not None else settings.HTTP_MAX_RETRIES))
        self._total_timeout_s = float(total_timeout_s if total_timeout_s is not None else settings.HTTP_TOTAL_TIMEOUT_S)
        self._backoff_base = float(backoff_base_s if backoff_base_s is not None else settings.HTTP_BACKOFF_BASE_S)
        self._backoff_max = float(backoff_max_s if backoff_max_s is not None else settings.HTTP_BACKOFF_MAX_S)
        self._retry_jitter = float(retry_jitter_s if retry_jitter_s is not None else settings.HTTP_BACKOFF_JITTER_S)
        configured_statuses = retry_status_codes if retry_status_codes is not None else settings.HTTP_RETRY_STATUS_CODES
        self._retry_status_codes = frozenset(configured_statuses or [])
        self._task_id = getattr(getattr(settings, "etl", None), "task_id", None)
        self._request_id = structlog_contextvars.get_contextvars().get("request_id")

    def _retry_after_for_response(self, response: httpx.Response) -> tuple[bool, float | None]:
        if response.status_code in self._retry_status_codes:
            return True, _parse_retry_after(response.headers.get("Retry-After"))
        return False, None

    def _new_wait(self) -> _RetryWait:
        return _RetryWait(multiplier=self._backoff_base, max=self._backoff_max, jitter=self._retry_jitter)

    def _record_outcome(self, method: str, outcome: str, duration: float) -> None:
        record_external_http_request(self.integration, method, outcome)
        observe_external_http_latency(self.integration, method, duration)

    def _log_retry(self, retry_state: RetryCallState, *, method: str, url: str) -> None:
        exc = retry_state.outcome.exception() if retry_state.outcome and retry_state.outcome.failed else None
        reason, status_code = _retry_reason(exc)
        record_external_http_retry(self.integration, method, reason)
        sleep_for = retry_state.next_action.sleep if retry_state.next_action else 0.0
        logger.warning(
            "external_http.retry",
            integration=self.integration,
            method=method,
            url=_safe_url(url),
            attempt=retry_state.attempt_number,
            sleep=float(sleep_for or 0.0),
            status_code=status_code,
            reason=reason,
            task_id=self._task_id,
            request_id=self._request_id,
        )

    def _before_sleep(self, *, method: str, url: str) -> Callable[[RetryCallState], None]:
        return lambda state: self._log_retry(state, method=method, url=url)

    def _before_sleep_async(self, *, method: str, url: str) -> Callable[[RetryCallState], Awaitable[None]]:
        async def _callback(state: RetryCallState) -> None:
            self._log_retry(state, method=method, url=url)

        return _callback

    def _extract_retry_error(self, exc: RetryError, *, url: str) -> tuple[Exception, int]:
        attempts = self._max_retries
        fut = getattr(exc, "last_attempt", None)
        if fut is not None:
            attempts = getattr(fut, "attempt_number", attempts)
            if fut.exception() is not None:
                return _convert_retry_exception(fut.exception(), url=url), attempts
            if isinstance(fut.result(), httpx.Response):
                result = fut.result()
                return (
                    httpx.HTTPStatusError(
                        f"HTTP {result.status_code}",
                        request=result.request,
                        response=result,
                    ),
                    attempts,
                )
        return HTTPClientError(f"HTTP request to {url} failed", original=exc), attempts


class HTTPClient(_BaseHTTPClient):
    """Synchronous HTTP client with shared retry, logging and metrics instrumentation."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        client_kwargs: dict[str, Any] = {
            "timeout": self._timeout,
            "limits": self._limits,
            "headers": self._headers,
            "transport": self._transport,
        }
        if self._base_url:
            client_kwargs["base_url"] = self._base_url
        self._client = httpx.Client(**client_kwargs)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HTTPClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _execute(
        self,
        *,
        method: str,
        url: str,
        action: Callable[[], httpx.Response],
        log_context: _RequestLog,
        cleanup: Callable[[], None] | None = None,
        allowed_statuses: frozenset[int] | None = None,
    ) -> httpx.Response:
        start = time.perf_counter()
        attempts = 0
        final_exc: Exception | None = None
        final_attempts = 0
        allowed = allowed_statuses or frozenset()
        retrying = Retrying(
            stop=stop_after_attempt(self._max_retries) | stop_after_delay(self._total_timeout_s),
            wait=self._new_wait(),
            retry=retry_if_exception(_is_retryable_exception),
            reraise=False,
            before_sleep=self._before_sleep(method=method, url=url),
        )
        try:
            for attempt in retrying:
                attempts += 1
                with attempt:
                    response = action()
                    should_retry, retry_after = self._retry_after_for_response(response)
                    if should_retry:
                        response.close()
                        raise RetryableStatusError(
                            f"HTTP {response.status_code}",
                            request=response.request,
                            response=response,
                            retry_after=retry_after,
                        )
                    if response.status_code in allowed:
                        duration = time.perf_counter() - start
                        self._record_outcome(method, "success", duration)
                        log_context.success(response.status_code, attempts=attempts)
                        return response
                    response.raise_for_status()
                    duration = time.perf_counter() - start
                    self._record_outcome(method, "success", duration)
                    log_context.success(response.status_code, attempts=attempts)
                    return response
        except RetryError as exc:
            if cleanup:
                cleanup()
            final_exc, final_attempts = self._extract_retry_error(exc, url=url)
            duration = time.perf_counter() - start
            self._record_outcome(method, "retry_exhausted", duration)
            log_context.failure(final_exc, attempts=final_attempts)
        except Exception as exc:
            if cleanup:
                cleanup()
            duration = time.perf_counter() - start
            outcome = "retry_exhausted" if attempts >= self._max_retries else _classify_exception(exc)
            self._record_outcome(method, outcome, duration)
            log_context.failure(exc, attempts=max(attempts, 1))
            raise
        if final_exc is not None:
            raise final_exc
        raise HTTPClientError(f"HTTP request to {url} failed unexpectedly")

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        method_name = (method or "GET").upper()
        allowed_statuses: frozenset[int] | None = None
        if "allowed_statuses" in kwargs:
            raw_allowed = kwargs.pop("allowed_statuses")
            if raw_allowed is not None:
                allowed_statuses = frozenset(int(code) for code in raw_allowed)
        log_context = _RequestLog(
            integration=self.integration,
            method=method_name,
            url=url,
            task_id=self._task_id,
            request_id=self._request_id,
        )
        log_context.start()
        return self._execute(
            method=method_name,
            url=url,
            action=lambda: self._client.request(method_name, url, **kwargs),
            log_context=log_context,
            allowed_statuses=allowed_statuses,
        )

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def get_json(self, url: str, **kwargs: Any) -> Any:
        response = self.get(url, **kwargs)
        try:
            return response.json()
        finally:
            response.close()

    def post_json(self, url: str, *, json: Any = None, **kwargs: Any) -> Any:
        response = self.post(url, json=json, **kwargs)
        try:
            return response.json()
        finally:
            response.close()

    def download_to_file(
        self,
        url: str,
        *,
        dest_path: Path,
        method: str = "GET",
        chunk_size: int = 1 << 20,
        on_chunk: Callable[[bytes], Any] | None = None,
        **kwargs: Any,
    ) -> Path:
        method_name = (method or "GET").upper()
        log_context = _RequestLog(
            integration=self.integration,
            method=method_name,
            url=url,
            task_id=self._task_id,
            request_id=self._request_id,
        )
        log_context.start()

        def _cleanup() -> None:
            with contextlib.suppress(FileNotFoundError):
                dest_path.unlink()

        def _stream() -> httpx.Response:
            with self._client.stream(method_name, url, **kwargs) as response:
                should_retry, retry_after = self._retry_after_for_response(response)
                if should_retry:
                    raise RetryableStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                        retry_after=retry_after,
                    )
                response.raise_for_status()
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with dest_path.open("wb") as handle:
                    for chunk in response.iter_bytes(chunk_size=chunk_size):
                        if on_chunk is not None:
                            on_chunk(chunk)
                        handle.write(chunk)
                return response

        response = self._execute(
            method=method_name,
            url=url,
            action=_stream,
            log_context=log_context,
            cleanup=_cleanup,
        )
        response.close()
        return dest_path


class AsyncHTTPClient(_BaseHTTPClient):
    """Asynchronous HTTP client with shared retry, logging and metrics instrumentation."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        client_kwargs: dict[str, Any] = {
            "timeout": self._timeout,
            "limits": self._limits,
            "headers": self._headers,
            "transport": self._transport,
        }
        if self._base_url:
            client_kwargs["base_url"] = self._base_url
        self._client = httpx.AsyncClient(**client_kwargs)

    async def __aenter__(self) -> AsyncHTTPClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    @property
    def httpx_client(self) -> httpx.AsyncClient:
        """Expose underlying httpx client for deprecated wrappers."""
        return self._client

    async def _close_response(self, response: httpx.Response) -> None:
        close = getattr(response, "aclose", None)
        if callable(close):
            await close()
        else:
            response.close()

    async def _execute(
        self,
        *,
        method: str,
        url: str,
        action: Callable[[], Awaitable[httpx.Response]],
        log_context: _RequestLog,
        cleanup: Callable[[], None] | None = None,
        allowed_statuses: frozenset[int] | None = None,
    ) -> httpx.Response:
        start = time.perf_counter()
        attempts = 0
        final_exc: Exception | None = None
        final_attempts = 0
        allowed = allowed_statuses or frozenset()
        retrying = AsyncRetrying(
            stop=stop_after_attempt(self._max_retries) | stop_after_delay(self._total_timeout_s),
            wait=self._new_wait(),
            retry=retry_if_exception(_is_retryable_exception),
            reraise=False,
            before_sleep=self._before_sleep_async(method=method, url=url),
        )
        try:
            async for attempt in retrying:
                attempts += 1
                with attempt:
                    response = await action()
                    should_retry, retry_after = self._retry_after_for_response(response)
                    if should_retry:
                        if hasattr(response, "aclose"):
                            await response.aclose()
                        else:
                            response.close()
                        raise RetryableStatusError(
                            f"HTTP {response.status_code}",
                            request=response.request,
                            response=response,
                            retry_after=retry_after,
                        )
                    if response.status_code in allowed:
                        duration = time.perf_counter() - start
                        self._record_outcome(method, "success", duration)
                        log_context.success(response.status_code, attempts=attempts)
                        return response
                    response.raise_for_status()
                    duration = time.perf_counter() - start
                    self._record_outcome(method, "success", duration)
                    log_context.success(response.status_code, attempts=attempts)
                    return response
        except RetryError as exc:
            if cleanup:
                cleanup()
            final_exc, final_attempts = self._extract_retry_error(exc, url=url)
            duration = time.perf_counter() - start
            self._record_outcome(method, "retry_exhausted", duration)
            log_context.failure(final_exc, attempts=final_attempts)
        except Exception as exc:
            if cleanup:
                cleanup()
            duration = time.perf_counter() - start
            outcome = "retry_exhausted" if attempts >= self._max_retries else _classify_exception(exc)
            self._record_outcome(method, outcome, duration)
            log_context.failure(exc, attempts=max(attempts, 1))
            raise
        if final_exc is not None:
            raise final_exc

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        method_name = (method or "GET").upper()
        allowed_statuses: frozenset[int] | None = None
        if "allowed_statuses" in kwargs:
            raw_allowed = kwargs.pop("allowed_statuses")
            if raw_allowed is not None:
                allowed_statuses = frozenset(int(code) for code in raw_allowed)
        log_context = _RequestLog(
            integration=self.integration,
            method=method_name,
            url=url,
            task_id=self._task_id,
            request_id=self._request_id,
        )
        log_context.start()
        return await self._execute(
            method=method_name,
            url=url,
            action=lambda: self._client.request(method_name, url, **kwargs),
            log_context=log_context,
            allowed_statuses=allowed_statuses,
        )

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def get_json(self, url: str, **kwargs: Any) -> Any:
        response = await self.get(url, **kwargs)
        try:
            return response.json()
        finally:
            await self._close_response(response)

    async def post_json(self, url: str, *, json: Any = None, **kwargs: Any) -> Any:
        response = await self.post(url, json=json, **kwargs)
        try:
            return response.json()
        finally:
            await self._close_response(response)

    async def download_to_file(
        self,
        url: str,
        *,
        dest_path: Path,
        method: str = "GET",
        chunk_size: int = 1 << 20,
        on_chunk: Callable[[bytes], Any] | None = None,
        **kwargs: Any,
    ) -> Path:
        method_name = (method or "GET").upper()
        log_context = _RequestLog(
            integration=self.integration,
            method=method_name,
            url=url,
            task_id=self._task_id,
            request_id=self._request_id,
        )
        log_context.start()

        def _cleanup() -> None:
            with contextlib.suppress(FileNotFoundError):
                dest_path.unlink()

        async def _stream() -> httpx.Response:
            async with self._client.stream(method_name, url, **kwargs) as response:
                should_retry, retry_after = self._retry_after_for_response(response)
                if should_retry:
                    raise RetryableStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                        retry_after=retry_after,
                    )
                response.raise_for_status()
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with dest_path.open("wb") as handle:
                    async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                        if on_chunk is not None:
                            maybe_awaitable = on_chunk(chunk)
                            if inspect.isawaitable(maybe_awaitable):
                                await maybe_awaitable
                        handle.write(chunk)
                return response

        response = await self._execute(
            method=method_name,
            url=url,
            action=_stream,
            log_context=log_context,
            cleanup=_cleanup,
        )
        await self._close_response(response)
        return dest_path
