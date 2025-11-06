from __future__ import annotations

import contextlib
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx
import structlog
from tenacity import (
    RetryCallState,
    RetryError,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
    wait_random_exponential,
)

from awa_common import metrics
from awa_common.settings import settings as SETTINGS

logger = structlog.get_logger(__name__)


class ETLHTTPError(Exception):
    """Wrap HTTP client errors with ETL context."""

    def __init__(
        self,
        message: str,
        *,
        source: str | None,
        url: str,
        task_id: str | None,
        status_code: int | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.source = source
        self.url = url
        self.task_id = task_id
        self.status_code = status_code
        self.request_id = request_id


class RetryableHTTPStatusError(Exception):
    """Internal exception used to trigger retries on retryable status codes."""

    def __init__(self, response: httpx.Response, retry_after: float | None = None) -> None:
        super().__init__(f"HTTP {response.status_code}")
        self.response = response
        self.retry_after = retry_after


def _default_timeout() -> httpx.Timeout:
    return httpx.Timeout(
        timeout=SETTINGS.ETL_TOTAL_TIMEOUT_S,
        connect=SETTINGS.ETL_CONNECT_TIMEOUT_S,
        read=SETTINGS.ETL_READ_TIMEOUT_S,
        write=SETTINGS.ETL_READ_TIMEOUT_S,
        pool=SETTINGS.ETL_CONNECT_TIMEOUT_S,
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
    with contextlib.suppress((TypeError, ValueError)):
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
                status_code = exc.response.status_code
                metric_code = str(status_code)
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
        "etl_http_retry",
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
        metrics.record_etl_retry(source, metric_code)


def _wrap_with_context(
    exc: Exception,
    *,
    source: str | None,
    url: str,
    task_id: str | None,
    request_id: str | None,
) -> ETLHTTPError:
    status: int | None = None
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
    elif isinstance(exc, RetryableHTTPStatusError):
        status = exc.response.status_code
    message = f"Failed to fetch {url}"
    return ETLHTTPError(
        message,
        source=source,
        url=url,
        task_id=task_id,
        status_code=status,
        request_id=request_id,
    )


def _run_with_retries(
    func: Callable[[], httpx.Response],
    *,
    source: str | None,
    url: str,
    task_id: str | None,
    request_id: str | None,
    total_timeout: float,
) -> httpx.Response:
    retrying = Retrying(
        stop=stop_after_attempt(SETTINGS.ETL_MAX_RETRIES) | stop_after_delay(total_timeout),
        wait=_RetryWait(multiplier=SETTINGS.ETL_BACKOFF_BASE_S, max=SETTINGS.ETL_BACKOFF_MAX_S),
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
    try:
        return retrying(func)
    except RetryError as exc:
        outcome = exc.last_attempt.outcome if exc.last_attempt is not None else None
        if outcome is not None:
            if outcome.failed:
                inner_exc = outcome.exception()
                raise _wrap_with_context(
                    inner_exc, source=source, url=url, task_id=task_id, request_id=request_id
                ) from exc
            result = outcome.result()
            if isinstance(result, httpx.Response):
                raise _wrap_with_context(
                    RetryableHTTPStatusError(result),
                    source=source,
                    url=url,
                    task_id=task_id,
                    request_id=request_id,
                ) from exc
        raise _wrap_with_context(exc, source=source, url=url, task_id=task_id, request_id=request_id) from exc
    except Exception as exc:  # pragma: no cover - safeguard
        raise _wrap_with_context(exc, source=source, url=url, task_id=task_id, request_id=request_id) from exc


def _prepare_client(timeout: Any) -> httpx.Client:
    resolved_timeout = timeout or _default_timeout()
    return httpx.Client(timeout=resolved_timeout)


def request(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    json: Any = None,
    data: Any = None,
    files: Any = None,
    timeout: Any = None,
    source: str | None = None,
    task_id: str | None = None,
    request_id: str | None = None,
) -> httpx.Response:
    """Perform an HTTP request with retries and structured logging."""

    def _do_request() -> httpx.Response:
        with _prepare_client(timeout) as client:
            response = client.request(
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
                response.close()
                raise RetryableHTTPStatusError(response, retry_after=retry_after)
            response.raise_for_status()
            return response

    return _run_with_retries(
        _do_request,
        source=source,
        url=url,
        task_id=task_id,
        request_id=request_id,
        total_timeout=SETTINGS.ETL_TOTAL_TIMEOUT_S,
    )


def download(
    url: str,
    *,
    dest_path: Path,
    chunk_size: int = 1 << 20,
    timeout: Any = None,
    source: str | None = None,
    task_id: str | None = None,
    request_id: str | None = None,
) -> Path:
    """Download a URL to a destination path with retries."""

    def _stream() -> httpx.Response:
        with _prepare_client(timeout) as client:
            with client.stream("GET", url) as response:
                if response.status_code in SETTINGS.ETL_RETRY_STATUS_CODES:
                    retry_after = _parse_retry_after(response.headers.get("Retry-After"))
                    raise RetryableHTTPStatusError(response, retry_after=retry_after)
                response.raise_for_status()
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with dest_path.open("wb") as handle:
                    for chunk in response.iter_bytes(chunk_size=chunk_size):
                        handle.write(chunk)
                return response

    try:
        _run_with_retries(
            _stream,
            source=source,
            url=url,
            task_id=task_id,
            request_id=request_id,
            total_timeout=SETTINGS.ETL_TOTAL_TIMEOUT_S,
        )
    except ETLHTTPError:
        with contextlib.suppress(FileNotFoundError):
            dest_path.unlink()
        raise
    return dest_path


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
            return min(retry_after, SETTINGS.ETL_BACKOFF_MAX_S)
        return super().__call__(retry_state)
