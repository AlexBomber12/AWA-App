from __future__ import annotations

import datetime as dt
import hashlib
import json
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from typing import Any

import sentry_sdk
import structlog
from cashews import Cache
from cashews.exceptions import CacheBackendInteractionError, NotConfiguredError

from awa_common.metrics import record_redis_error

logger = structlog.get_logger(__name__)

cache = Cache("awa-cache")
_DEFAULT_BACKEND_URL = "mem://"
_DEFAULT_BACKEND_PREFIX = ""
_current_backend_url = _DEFAULT_BACKEND_URL
_current_backend_prefix = _DEFAULT_BACKEND_PREFIX
cache.setup(_DEFAULT_BACKEND_URL, prefix=_DEFAULT_BACKEND_PREFIX)


def normalize_namespace(namespace: str | None) -> str:
    """Ensure namespaces end with a colon so prefixes remain readable."""
    raw = (namespace or "stats:").strip()
    if not raw.endswith(":"):
        raw = f"{raw}:"
    return raw


def build_cache_key(
    namespace: str,
    endpoint: str,
    params: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
) -> str:
    """Return a namespaced cache key hashed from endpoint + sorted params."""
    pairs: list[tuple[str, Any]] = []
    if params:
        if isinstance(params, Mapping):
            items = params.items()
        else:
            items = params
        for key, value in items:
            pairs.append((str(key), _stringify(value)))
    pairs.sort(key=lambda item: (item[0], item[1]))
    payload = json.dumps(
        {"endpoint": endpoint.strip().lower(), "params": pairs},
        separators=(",", ":"),
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    safe_namespace = normalize_namespace(namespace)
    endpoint_label = endpoint.strip().lower().replace("/", "_") or "unknown"
    return f"{safe_namespace}{endpoint_label}:{digest}"


async def configure_cache_backend(
    url: str,
    *,
    prefix: str = "",
    suppress: bool = False,
    **kwargs: Any,
) -> None:
    """Configure the shared cache backend, closing any existing connections."""
    global _current_backend_url, _current_backend_prefix
    await cache.close()
    cache.setup(url, prefix=prefix, suppress=suppress, **kwargs)
    _current_backend_url = url
    _current_backend_prefix = prefix
    logger.info("cache_backend_configured", url=url, prefix=prefix or "")


async def close_cache() -> None:
    """Close any active cache backend connections."""
    await cache.close()


async def ping_cache() -> bool:
    """Return True when the cache backend is reachable."""
    try:
        await cache.ping()
        return True
    except (CacheBackendInteractionError, NotConfiguredError) as exc:
        _log_cache_error("stats_cache", "ping", exc)
        return False


async def get_json(key: str) -> Any | None:
    """Return the cached payload or None when missing or on backend errors."""
    result = await _call_cache("stats_cache", "get", cache.get(key), key=key)
    return result


async def set_json(key: str, value: Any, ttl_s: int) -> bool:
    """Store a payload with TTL, returning False when disabled or errors occur."""
    if ttl_s <= 0:
        return False
    stored = await _call_cache("stats_cache", "set", cache.set(key, value, expire=float(ttl_s)), key=key)
    return bool(stored)


def returns_metadata_key(cache_key: str) -> str:
    return f"{cache_key}:meta"


async def set_returns_metadata(
    cache_key: str,
    *,
    date_from: dt.date | None,
    date_to: dt.date | None,
    ttl_s: int,
) -> None:
    payload = {
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
    }
    await set_json(returns_metadata_key(cache_key), payload, ttl_s)


async def purge_prefix(
    prefix: str,
    *,
    batch_size: int = 200,
) -> int:
    """Delete keys matching the prefix using SCAN semantics."""
    pattern = f"{prefix}*"
    deleted = 0
    try:
        async for batch in _batched_scan(pattern, batch_size=batch_size):
            await cache.delete_many(*batch)
            deleted += len(batch)
    except (CacheBackendInteractionError, NotConfiguredError) as exc:
        _log_cache_error("stats_cache", "delete_match", exc, key=prefix)
    return deleted


async def purge_returns_cache(
    namespace: str,
    *,
    date_from: dt.date | None,
    date_to: dt.date | None,
    batch_size: int = 200,
) -> int:
    """Delete returns caches that overlap the refreshed window."""
    normalized_ns = normalize_namespace(namespace)
    if date_from is None or date_to is None:
        return await purge_prefix(f"{normalized_ns}returns", batch_size=batch_size)

    pattern = f"{normalized_ns}returns*:meta"
    deleted = 0
    try:
        async for batch in _batched_scan(pattern, batch_size=batch_size):
            to_delete: list[str] = []
            for key in batch:
                meta = await get_json(key)
                if not _meta_overlaps(meta, date_from, date_to):
                    continue
                base_key = key[: -len(":meta")] if key.endswith(":meta") else key
                to_delete.append(key)
                to_delete.append(base_key)
            if to_delete:
                await cache.delete_many(*to_delete)
                deleted += len(to_delete)
    except (CacheBackendInteractionError, NotConfiguredError) as exc:
        _log_cache_error("stats_cache", "delete_returns", exc, key=normalized_ns)
    return deleted


def cached(
    *, ttl: float | int | str, key: str, namespace: str | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Return a decorator that caches function results using the configured cache."""
    full_key = key
    if namespace:
        full_key = f"{normalize_namespace(namespace)}{key}"
    return cache.cache(ttl=ttl, key=full_key)


async def _batched_scan(pattern: str, *, batch_size: int) -> AsyncIterator[list[str]]:
    batch: list[str] = []
    async for key in cache.scan(pattern, batch_size=batch_size):
        batch.append(key)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


async def _call_cache(
    operation: str,
    command: str,
    call: Awaitable[Any],
    *,
    key: str | None = None,
) -> Any | None:
    try:
        return await call
    except (CacheBackendInteractionError, NotConfiguredError) as exc:
        _log_cache_error(operation, command, exc, key=key)
        return None


def _log_cache_error(operation: str, command: str, exc: Exception, *, key: str | None = None) -> None:
    logger.warning(
        "cache_command_failed",
        operation=operation,
        command=command,
        key=key,
        backend=_current_backend_url,
        prefix=_current_backend_prefix,
        error=str(exc),
    )
    record_redis_error(operation, command, key=key)
    try:
        sentry_sdk.capture_exception(exc)
    except Exception:
        pass


def _meta_overlaps(meta: Any, window_start: dt.date, window_end: dt.date) -> bool:
    if not isinstance(meta, dict):
        return True
    start = _parse_date(meta.get("date_from"))
    end = _parse_date(meta.get("date_to"))
    if start is None or end is None:
        return True
    return not (end < window_start or window_end < start)


def _parse_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str) and value:
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _stringify(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, (int, float, bool, str)):
        return str(value)
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return ",".join(_stringify(item) for item in value)
    return json.dumps(value, sort_keys=True, default=str)


__all__ = [
    "build_cache_key",
    "cache",
    "cached",
    "close_cache",
    "configure_cache_backend",
    "get_json",
    "normalize_namespace",
    "ping_cache",
    "purge_prefix",
    "purge_returns_cache",
    "returns_metadata_key",
    "set_json",
    "set_returns_metadata",
]
