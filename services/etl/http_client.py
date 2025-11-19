"""Deprecated async HTTP helpers. Use awa_common.http_client.AsyncHTTPClient instead."""

from __future__ import annotations

import asyncio
import warnings
from typing import Any

import httpx

from awa_common.http_client import AsyncHTTPClient, RetryableStatusError

_CLIENTS: dict[str, AsyncHTTPClient] = {}
_LOCK = asyncio.Lock()
_DEFAULT_KEY = "etl_async"


async def _ensure_client(source: str | None = None) -> AsyncHTTPClient:
    key = (source or _DEFAULT_KEY).strip().lower() or _DEFAULT_KEY
    client = _CLIENTS.get(key)
    if client is not None:
        return client
    async with _LOCK:
        client = _CLIENTS.get(key)
        if client is None:
            client = AsyncHTTPClient(integration=key)
            _CLIENTS[key] = client
        return client


async def init_http(force: bool = False) -> AsyncHTTPClient:
    """Deprecated: initialize the shared async HTTP client."""
    warnings.warn(
        "services.etl.http_client is deprecated; use awa_common.http_client.AsyncHTTPClient instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if force:
        await close_http()
    return await _ensure_client()


async def close_http() -> None:
    """Deprecated: close all cached async HTTP clients."""
    warnings.warn(
        "services.etl.http_client is deprecated; use awa_common.http_client.AsyncHTTPClient instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    clients = list(_CLIENTS.values())
    _CLIENTS.clear()
    for client in clients:
        await client.aclose()


async def close_http_client() -> None:
    """Compatibility alias for close_http."""
    await close_http()


async def get_client() -> httpx.AsyncClient:
    """Deprecated: return the shared httpx.AsyncClient used by the wrapper."""
    warnings.warn(
        "services.etl.http_client.get_client is deprecated; use awa_common.http_client.AsyncHTTPClient instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    client = await _ensure_client()
    httpx_client: httpx.AsyncClient = client.httpx_client
    return httpx_client


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
    """Deprecated wrapper for AsyncHTTPClient.request."""
    warnings.warn(
        "services.etl.http_client.request is deprecated; use awa_common.http_client.AsyncHTTPClient instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    client = await _ensure_client(source)
    response: httpx.Response = await client.request(
        method,
        url,
        params=params,
        headers=headers,
        json=json,
        data=data,
        files=files,
    )
    return response


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
    """Deprecated wrapper for AsyncHTTPClient JSON responses."""
    warnings.warn(
        "services.etl.http_client.fetch_json is deprecated; use awa_common.http_client.AsyncHTTPClient instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    client = await _ensure_client(source)
    return await client.get_json(
        url,
        params=params,
        headers=headers,
        json=json,
        data=data,
        files=files,
    )


request_json = fetch_json


RetryableHTTPStatusError = RetryableStatusError
