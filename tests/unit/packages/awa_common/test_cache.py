from __future__ import annotations

import asyncio
import datetime as dt

import pytest
from cashews.exceptions import CacheBackendInteractionError

from awa_common import cache


def test_normalize_namespace_appends_colon():
    assert cache.normalize_namespace("stats") == "stats:"
    assert cache.normalize_namespace("stats:") == "stats:"


def test_stats_cache_key_stability():
    namespace = "stats:"
    params_a = {"vendor": "Acme", "date_from": "2024-01-01"}
    params_b = [("date_from", "2024-01-01"), ("vendor", "Acme")]
    key_a = cache.build_cache_key(namespace, "returns", params_a)
    key_b = cache.build_cache_key(namespace, "returns", list(reversed(params_b)))
    assert key_a == key_b
    key_c = cache.build_cache_key(namespace, "returns", {"vendor": "Other"})
    assert key_c != key_a


@pytest.mark.asyncio
@pytest.mark.real_sleep
async def test_stats_cache_ttl_roundtrip():
    await cache.cache.clear()
    key = cache.build_cache_key("stats:", "kpi", None)
    assert await cache.set_json(key, {"value": 1}, ttl_s=1)
    assert await cache.get_json(key) == {"value": 1}
    await asyncio.sleep(0.5)
    assert await cache.get_json(key) == {"value": 1}
    await asyncio.sleep(1.2)
    assert await cache.get_json(key) is None


@pytest.mark.asyncio
async def test_get_json_handles_errors(monkeypatch):
    await cache.cache.clear()

    async def broken_get(*_args, **_kwargs):
        raise CacheBackendInteractionError()

    errors = []

    class DummyLogger:
        def warning(self, event, **kwargs):
            errors.append((event, kwargs))

    recorded = []
    monkeypatch.setattr(cache, "logger", DummyLogger())
    monkeypatch.setattr(cache, "record_redis_error", lambda *args, **kwargs: recorded.append((args, kwargs)))
    monkeypatch.setattr(cache.cache, "get", broken_get, raising=False)

    assert await cache.get_json("key") is None
    assert errors, "expected cache errors to be logged"
    assert recorded, "expected redis error metric"


@pytest.mark.asyncio
async def test_set_json_handles_errors(monkeypatch):
    await cache.cache.clear()

    async def broken_set(*_args, **_kwargs):
        raise CacheBackendInteractionError()

    errors = []

    class DummyLogger:
        def warning(self, event, **kwargs):
            errors.append((event, kwargs))

    recorded = []
    monkeypatch.setattr(cache, "logger", DummyLogger())
    monkeypatch.setattr(cache, "record_redis_error", lambda *args, **kwargs: recorded.append((args, kwargs)))
    monkeypatch.setattr(cache.cache, "set", broken_set, raising=False)

    assert not await cache.set_json("stats:key", {"ok": True}, ttl_s=5)
    assert not await cache.set_json("stats:key", {"ok": True}, ttl_s=0)
    assert errors and recorded


@pytest.mark.asyncio
async def test_set_returns_metadata_records_window():
    await cache.cache.clear()
    key = cache.build_cache_key("stats:", "returns", None)
    await cache.set_returns_metadata(
        key,
        date_from=None,
        date_to=None,
        ttl_s=5,
    )
    meta_key = cache.returns_metadata_key(key)
    assert await cache.get_json(meta_key) == {"date_from": None, "date_to": None}


@pytest.mark.asyncio
async def test_purge_prefix_and_returns_cache():
    await cache.cache.clear()
    await cache.set_json("stats:kpi:1", {}, ttl_s=5)
    await cache.set_json("stats:kpi:2", {}, ttl_s=5)
    deleted = await cache.purge_prefix("stats:kpi")
    assert deleted == 2
    hit_key = "stats:returns:hit"
    await cache.set_json(hit_key, {}, ttl_s=5)
    await cache.set_json(
        cache.returns_metadata_key(hit_key),
        {"date_from": "2024-01-01", "date_to": "2024-01-07"},
        ttl_s=5,
    )
    miss_key = "stats:returns:miss"
    await cache.set_json(miss_key, {}, ttl_s=5)
    await cache.set_json(
        cache.returns_metadata_key(miss_key),
        {"date_from": "2023-01-01", "date_to": "2023-01-02"},
        ttl_s=5,
    )
    deleted = await cache.purge_returns_cache(
        "stats:",
        date_from=None,
        date_to=None,
    )
    assert deleted >= 2
    await cache.set_json("stats:returns:all", {}, ttl_s=5)
    await cache.set_json(
        "stats:returns:all:meta",
        {"date_from": "2024-01-02", "date_to": "2024-01-05"},
        ttl_s=5,
    )
    deleted = await cache.purge_returns_cache(
        "stats:",
        date_from=dt.date(2024, 1, 1),
        date_to=dt.date(2024, 1, 10),
    )
    assert deleted >= 2


def test_meta_overlap_helpers():
    window_start = dt.date(2024, 1, 1)
    window_end = dt.date(2024, 1, 10)
    assert cache._meta_overlaps({"date_from": "2024-01-02", "date_to": "2024-01-03"}, window_start, window_end)
    assert not cache._meta_overlaps({"date_from": "2023-01-01", "date_to": "2023-01-05"}, window_start, window_end)
