"""Deprecated ETL HTTP helpers. Use awa_common.http_client instead."""

from __future__ import annotations

import contextlib
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from awa_common import metrics as _metrics
from awa_common.http_client import (
    HTTPClient,
    HTTPClientError,
    RetryableStatusError,
    _RetryWait as _CoreRetryWait,
)

_CLIENTS: dict[str, HTTPClient] = {}
metrics = _metrics


def _retry_reason_label(exc: Exception | None) -> str:
    if isinstance(exc, RetryableStatusError) and exc.response is not None:
        return str(exc.response.status_code)
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return str(exc.response.status_code)
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if exc is None:
        return "unknown"
    return exc.__class__.__name__


class _ETLHTTPClient(HTTPClient):
    def _log_retry(self, retry_state, *, method: str, url: str) -> None:
        super()._log_retry(retry_state, method=method, url=url)
        source = getattr(self, "integration", None)
        exc = retry_state.outcome.exception() if retry_state.outcome and retry_state.outcome.failed else None
        reason = _retry_reason_label(exc)
        if source:
            metrics.record_etl_retry(source, reason)


class ETLHTTPError(HTTPClientError):
    """Deprecated ETL HTTP exception preserving legacy attributes."""

    def __init__(
        self,
        message: str,
        *,
        source: str | None,
        url: str,
        task_id: str | None,
        status_code: int | None,
        request_id: str | None,
        original: Exception | None = None,
    ) -> None:
        super().__init__(message, original=original)
        self.source = source
        self.url = url
        self.task_id = task_id
        self.status_code = status_code
        self.request_id = request_id


def _client_for(source: str | None) -> HTTPClient:
    key = (source or "etl_http").strip().lower() or "etl_http"
    client = _CLIENTS.get(key)
    if client is None:
        client = _ETLHTTPClient(integration=key)
        _CLIENTS[key] = client
    return client


def _run_with_retries(func: Callable[[], httpx.Response], **kwargs: Any) -> httpx.Response:
    return func()


def _wrap_exception(
    exc: Exception,
    *,
    source: str | None,
    url: str,
    task_id: str | None,
    request_id: str | None,
) -> ETLHTTPError:
    status_code: int | None = None
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        status_code = exc.response.status_code
    message = f"Failed to fetch {url}"
    return ETLHTTPError(
        message,
        source=source,
        url=url,
        task_id=task_id,
        status_code=status_code,
        request_id=request_id,
        original=exc,
    )


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
    """Deprecated wrapper around awa_common.http_client.HTTPClient.request."""
    warnings.warn(
        "awa_common.etl.http is deprecated; use awa_common.http_client.HTTPClient instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    client = _client_for(source)
    try:
        return client.request(
            method,
            url,
            params=params,
            headers=headers,
            json=json,
            data=data,
            files=files,
            timeout=timeout,
        )
    except Exception as exc:  # pragma: no cover - compatibility shim
        raise _wrap_exception(exc, source=source, url=url, task_id=task_id, request_id=request_id) from exc


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
    """Deprecated wrapper around awa_common.http_client.HTTPClient.download_to_file."""
    warnings.warn(
        "awa_common.etl.http is deprecated; use awa_common.http_client.HTTPClient instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    client = _client_for(source)

    def _download_action() -> Path:
        client.download_to_file(
            url,
            dest_path=dest_path,
            chunk_size=chunk_size,
            method="GET",
            timeout=timeout,
        )
        return dest_path

    try:
        return _run_with_retries(_download_action, source=source)
    except Exception as exc:  # pragma: no cover - compatibility shim
        with contextlib.suppress(FileNotFoundError):
            dest_path.unlink()
        raise _wrap_exception(exc, source=source, url=url, task_id=task_id, request_id=request_id) from exc


class RetryableHTTPStatusError(RetryableStatusError):
    """Backward-compatible exception for tests expecting the legacy constructor."""

    def __init__(self, response: httpx.Response, retry_after: float | None = None) -> None:
        message = f"HTTP {response.status_code}"
        super().__init__(message, request=response.request, response=response, retry_after=retry_after)


class _RetryWait(_CoreRetryWait):
    """Expose legacy _RetryWait for tests."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if "jitter" not in kwargs:
            kwargs["jitter"] = 0.0
        super().__init__(*args, **kwargs)
