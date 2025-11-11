from __future__ import annotations

import datetime as dt
import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

try:  # pragma: no cover - redis is optional when cache is disabled
    import redis.asyncio as aioredis
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore[assignment]


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


async def get_json(redis_client: aioredis.Redis | None, key: str) -> Any | None:
    """Return decoded JSON for the cache key or None when missing."""
    if redis_client is None:
        return None
    try:
        raw = await redis_client.get(key)
    except Exception:
        return None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


async def set_json(redis_client: aioredis.Redis | None, key: str, value: Any, ttl_s: int) -> bool:
    """Store JSON payload with TTL."""
    if redis_client is None or ttl_s <= 0:
        return False
    try:
        payload = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError):
        return False
    try:
        await redis_client.set(key, payload, ex=max(int(ttl_s), 1))
        return True
    except Exception:
        return False


def returns_metadata_key(cache_key: str) -> str:
    return f"{cache_key}:meta"


async def set_returns_metadata(
    redis_client: aioredis.Redis | None,
    cache_key: str,
    *,
    date_from: dt.date | None,
    date_to: dt.date | None,
    ttl_s: int,
) -> None:
    if redis_client is None or ttl_s <= 0:
        return
    payload = {
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
    }
    await set_json(redis_client, returns_metadata_key(cache_key), payload, ttl_s)


async def purge_prefix(
    redis_client: aioredis.Redis | None,
    prefix: str,
    *,
    batch_size: int = 250,
) -> int:
    """Delete keys matching the prefix using SCAN + pipeline."""
    if redis_client is None:
        return 0
    pattern = f"{prefix}*"
    deleted = 0
    pipeline = redis_client.pipeline(transaction=False)
    queued = 0
    try:
        async for key in redis_client.scan_iter(match=pattern, count=batch_size):
            pipeline.delete(key)
            queued += 1
            if queued >= batch_size:
                deleted += sum(await pipeline.execute())
                pipeline = redis_client.pipeline(transaction=False)
                queued = 0
        if queued:
            deleted += sum(await pipeline.execute())
    except Exception:
        return deleted
    return deleted


async def purge_returns_cache(
    redis_client: aioredis.Redis | None,
    namespace: str,
    *,
    date_from: dt.date | None,
    date_to: dt.date | None,
    batch_size: int = 200,
) -> int:
    """Delete returns caches that overlap the refreshed window."""
    if redis_client is None:
        return 0
    normalized_ns = normalize_namespace(namespace)
    if date_from is None or date_to is None:
        # No window hint — drop all returns entries.
        return await purge_prefix(redis_client, f"{normalized_ns}returns")

    pattern = f"{normalized_ns}returns*:meta"
    deleted = 0
    pipeline = redis_client.pipeline(transaction=False)
    queued = 0
    try:
        async for key in redis_client.scan_iter(match=pattern, count=batch_size):
            meta = await get_json(redis_client, key)
            if not _meta_overlaps(meta, date_from, date_to):
                continue
            base_key = key[: -len(":meta")] if key.endswith(":meta") else key
            pipeline.delete(key)
            pipeline.delete(base_key)
            queued += 2
            if queued >= batch_size:
                deleted += sum(await pipeline.execute())
                pipeline = redis_client.pipeline(transaction=False)
                queued = 0
        if queued:
            deleted += sum(await pipeline.execute())
    except Exception:
        return deleted
    return deleted


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
    "get_json",
    "normalize_namespace",
    "purge_prefix",
    "purge_returns_cache",
    "returns_metadata_key",
    "set_json",
    "set_returns_metadata",
]
