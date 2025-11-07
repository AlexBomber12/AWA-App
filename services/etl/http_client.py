from __future__ import annotations

import asyncio
import atexit
import logging
from typing import Any

import httpx
from awa_common.etl.http import HTTPClientSettings, http_settings

logger = logging.getLogger(__name__)

_HTTP_CLIENT: httpx.AsyncClient | None = None
_HTTP_LOCK: asyncio.Lock | None = None
_HTTP_LOCK_LOOP: asyncio.AbstractEventLoop | None = None


def _ensure_lock(loop: asyncio.AbstractEventLoop) -> asyncio.Lock:
    global _HTTP_LOCK, _HTTP_LOCK_LOOP
    if _HTTP_LOCK is None or _HTTP_LOCK_LOOP is not loop:
        _HTTP_LOCK = asyncio.Lock()
        _HTTP_LOCK_LOOP = loop
    return _HTTP_LOCK


def _build_client(config: HTTPClientSettings) -> httpx.AsyncClient:
    timeout = httpx.Timeout(
        config.total_timeout,
        connect=config.connect_timeout,
        read=config.read_timeout,
        write=config.read_timeout,
        pool=config.pool_timeout,
    )
    limits = httpx.Limits(
        max_connections=config.max_connections,
        max_keepalive_connections=config.max_keepalive,
    )
    return httpx.AsyncClient(
        timeout=timeout, limits=limits, follow_redirects=config.follow_redirects
    )


async def get_http_client() -> httpx.AsyncClient:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is not None:
        return _HTTP_CLIENT
    loop = asyncio.get_running_loop()
    lock = _ensure_lock(loop)
    async with lock:
        if _HTTP_CLIENT is None:
            _HTTP_CLIENT = _build_client(http_settings)
        return _HTTP_CLIENT


async def close_http_client() -> None:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None:
        return
    loop = asyncio.get_running_loop()
    lock = _ensure_lock(loop)
    async with lock:
        client = _HTTP_CLIENT
        _HTTP_CLIENT = None
    if client is not None:
        await client.aclose()


async def request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    """Execute an HTTP request with shared retries and pool limits."""

    retries = http_settings.retries
    backoff = http_settings.retry_backoff_min
    attempt = 0
    last_error: Exception | None = None
    while attempt <= retries:
        try:
            client = await get_http_client()
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status not in http_settings.retry_status_codes and not 500 <= status < 600:
                raise
            last_error = exc
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            last_error = exc
        if attempt >= retries:
            break
        sleep_for = min(http_settings.retry_backoff_max, backoff)
        logger.debug(
            "HTTP %s %s failed (attempt %s/%s), retrying in %.2fs",
            method,
            url,
            attempt + 1,
            retries + 1,
            sleep_for,
        )
        await asyncio.sleep(sleep_for)
        backoff = min(http_settings.retry_backoff_max, backoff * 2)
        attempt += 1
    if last_error is not None:
        raise last_error
    raise RuntimeError("HTTP request failed without an exception")


def close_http_client_sync() -> None:
    """Best-effort synchronous shutdown hook used at interpreter exit."""

    if _HTTP_CLIENT is None:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(close_http_client())
    else:  # pragma: no cover - background shutdown in running loop
        loop.create_task(close_http_client())


atexit.register(close_http_client_sync)

__all__ = ["get_http_client", "close_http_client", "close_http_client_sync", "request"]
