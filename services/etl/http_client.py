from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
import structlog
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_random_exponential,
)

from awa_common.metrics import record_etl_retry, record_http_client_request
from awa_common.settings import settings as SETTINGS

logger = structlog.get_logger(__name__)


# Keep a handful of idle sockets alive so repeated cron invocations avoid TLS warmups.
HTTP_POOL_KEEPALIVE_CONNECTIONS = max(0, int(SETTINGS.ETL_HTTP_KEEPALIVE))
# Cap concurrent upstream calls (default 20) to avoid exhausting Keepa/Helium quotas.
HTTP_POOL_MAX_CONNECTIONS = max(HTTP_POOL_KEEPALIVE_CONNECTIONS, int(SETTINGS.ETL_HTTP_MAX_CONNECTIONS))
# Limit how long tasks wait for a pooled connection; defaults to the connect timeout (10s).
HTTP_POOL_TIMEOUT_S = float(SETTINGS.ETL_POOL_TIMEOUT_S or SETTINGS.ETL_CONNECT_TIMEOUT_S)
# Use the same retry budget as the sync ETL client (defaults to 3 attempts).
HTTP_MAX_RETRIES = max(1, int(SETTINGS.ETL_RETRY_ATTEMPTS))
# Abort retry loops after the global ETL timeout (defaults to 60s).
HTTP_TOTAL_TIMEOUT_S = float(SETTINGS.ETL_TOTAL_TIMEOUT_S)
HTTP_BACKOFF_BASE_S = float(SETTINGS.ETL_RETRY_BASE_S)
HTTP_BACKOFF_MAX_S = float(SETTINGS.ETL_RETRY_MAX_S)

_HTTP_CLIENT: httpx.AsyncClient | None = None
_HTTP_CLIENT_LOCK = asyncio.Lock()


class RetryableHTTPStatusError(httpx.HTTPStatusError):
    def __init__(
        self, message: str, *, request: httpx.Request, response: httpx.Response, retry_after: float | None
    ) -> None:
        super().__init__(message, request=request, response=response)
        self.retry_after = retry_after


def _default_timeout() -> httpx.Timeout:
    return httpx.Timeout(
        connect=SETTINGS.ETL_CONNECT_TIMEOUT_S,
        read=SETTINGS.ETL_READ_TIMEOUT_S,
        write=SETTINGS.ETL_READ_TIMEOUT_S,
        pool=HTTP_POOL_TIMEOUT_S,
    )


def _client_limits() -> httpx.Limits:
    return httpx.Limits(
        max_connections=HTTP_POOL_MAX_CONNECTIONS,
        max_keepalive_connections=HTTP_POOL_KEEPALIVE_CONNECTIONS,
    )


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if value.isdigit():
        try:
            seconds = float(value)
        except ValueError:
            return None
        return max(0.0, seconds)
    with contextlib.suppress(TypeError, ValueError):
        dt = parsedate_to_datetime(value)
        if dt:
            now = datetime.now(UTC)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return max(0.0, (dt - now).total_seconds())
    return None


def _before_sleep(
    retry_state: RetryCallState,
    *,
    source: str | None,
    url: str,
    task_id: str | None,
    request_id: str | None,
) -> None:
    sleep = 0.0
    status_code: int | None = None
    metric_code: str | None = None
    if retry_state.outcome is not None:
        if retry_state.outcome.failed:
            exc = retry_state.outcome.exception()
            if isinstance(exc, RetryableHTTPStatusError):
                status_code = exc.response.status_code if exc.response else None
                metric_code = str(status_code) if status_code is not None else None
            elif isinstance(exc, httpx.HTTPStatusError):
                status_code = exc.response.status_code if exc.response is not None else None
                metric_code = str(status_code) if status_code is not None else exc.__class__.__name__
            else:
                metric_code = exc.__class__.__name__
        else:
            result = retry_state.outcome.result()
            if isinstance(result, httpx.Response):
                status_code = result.status_code
                metric_code = str(status_code)
    if retry_state.next_action is not None:
        sleep = retry_state.next_action.sleep
    logger.warning(
        "etl_async_http_retry",
        attempt=retry_state.attempt_number,
        sleep=float(sleep),
        status_code=status_code,
        source=source,
        url=url,
        task_id=task_id,
        request_id=request_id,
        service=SETTINGS.SERVICE_NAME,
        env=SETTINGS.APP_ENV,
        version=SETTINGS.APP_VERSION,
    )
    if source and metric_code:
        record_etl_retry(source, metric_code)


class _RetryWait(wait_random_exponential):
    def __call__(self, retry_state: RetryCallState) -> float:
        retry_after: float | None = None
        if retry_state.outcome is not None:
            if retry_state.outcome.failed:
                exc = retry_state.outcome.exception()
                if isinstance(exc, RetryableHTTPStatusError):
                    retry_after = exc.retry_after
            else:
                result = retry_state.outcome.result()
                if isinstance(result, httpx.Response):
                    retry_after = _parse_retry_after(result.headers.get("Retry-After"))
        if retry_after is not None:
            return min(retry_after, HTTP_BACKOFF_MAX_S)
        return super().__call__(retry_state)


async def _ensure_client() -> httpx.AsyncClient:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is not None:
        return _HTTP_CLIENT
    async with _HTTP_CLIENT_LOCK:
        if _HTTP_CLIENT is None:
            _HTTP_CLIENT = httpx.AsyncClient(timeout=_default_timeout(), limits=_client_limits())
    if _HTTP_CLIENT is None:  # pragma: no cover
        raise RuntimeError("HTTP client initialisation failed")
    return _HTTP_CLIENT


async def init_http(force: bool = False) -> httpx.AsyncClient:
    if force:
        await close_http()
    return await _ensure_client()


async def get_client() -> httpx.AsyncClient:
    return await _get_client()


async def _get_client() -> httpx.AsyncClient:  # pragma: no cover - compatibility for older imports
    return await _ensure_client()


async def close_http() -> None:
    global _HTTP_CLIENT
    client = _HTTP_CLIENT
    if client is None:
        return
    _HTTP_CLIENT = None
    await client.aclose()


async def _run_with_retries(
    func: Callable[[], Awaitable[httpx.Response]],
    *,
    source: str | None,
    url: str,
    task_id: str | None,
    request_id: str | None,
) -> httpx.Response:
    retrying = AsyncRetrying(
        stop=stop_after_attempt(HTTP_MAX_RETRIES) | stop_after_delay(HTTP_TOTAL_TIMEOUT_S),
        wait=_RetryWait(multiplier=HTTP_BACKOFF_BASE_S, max=HTTP_BACKOFF_MAX_S),
        retry=retry_if_exception_type((httpx.RequestError, RetryableHTTPStatusError)),
        reraise=True,
        before_sleep=lambda state: _before_sleep(
            state,
            source=source,
            url=url,
            task_id=task_id,
            request_id=request_id,
        ),
    )
    async for attempt in retrying:  # pragma: no cover - tenacity handles loop
        with attempt:
            return await func()
    raise RuntimeError("Retry loop exhausted without returning")


async def request(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    json: Any = None,
    data: Any = None,
    files: Any = None,
    source: str | None = None,
    task_id: str | None = None,
    request_id: str | None = None,
) -> httpx.Response:
    client = await get_client()

    async def _send() -> httpx.Response:
        response = await client.request(
            method,
            url,
            params=params,
            headers=headers,
            json=json,
            data=data,
            files=files,
        )
        if response.status_code in SETTINGS.ETL_RETRY_STATUS_CODES:
            retry_after = _parse_retry_after(response.headers.get("Retry-After"))
            request_obj = response.request
            response.close()
            raise RetryableHTTPStatusError(
                f"HTTP {response.status_code}",
                request=request_obj,
                response=response,
                retry_after=retry_after,
            )
        response.raise_for_status()
        return response

    return await _run_with_retries(
        _send,
        source=source,
        url=url,
        task_id=task_id,
        request_id=request_id,
    )


async def fetch_json(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    json: Any = None,
    data: Any = None,
    files: Any = None,
    source: str | None = None,
    task_id: str | None = None,
    request_id: str | None = None,
) -> Any:
    loop = asyncio.get_running_loop()
    start = loop.time()
    try:
        response = await request(
            method,
            url,
            params=params,
            headers=headers,
            json=json,
            data=data,
            files=files,
            source=source,
            task_id=task_id,
            request_id=request_id,
        )
    except Exception as exc:
        duration_s = loop.time() - start
        status_code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) and exc.response else None
        logger.warning(
            "etl_http.request_failed",
            component="etl_http_client",
            method=method,
            url=url,
            status_code=status_code,
            duration_ms=int(duration_s * 1000),
            source=source,
            task_id=task_id,
            request_id=request_id,
        )
        record_http_client_request(source or "unknown", method, status_code, duration_s)
        raise

    duration_s = loop.time() - start
    try:
        payload = response.json()
    finally:
        response.close()
    record_http_client_request(source or "unknown", method, response.status_code, duration_s)
    logger.info(
        "etl_http.request_completed",
        component="etl_http_client",
        method=method,
        url=url,
        status_code=response.status_code,
        duration_ms=int(duration_s * 1000),
        source=source,
        task_id=task_id,
        request_id=request_id,
    )
    return payload


# Backwards compatibility for older imports
request_json = fetch_json
close_http_client = close_http
