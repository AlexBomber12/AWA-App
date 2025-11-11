from __future__ import annotations

import asyncio
import json

import pytest

from awa_common import cache
from tests.fakes import FakeRedis


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
    redis = FakeRedis()
    key = cache.build_cache_key("stats:", "kpi", None)
    assert await cache.set_json(redis, key, {"value": 1}, ttl_s=1)
    assert await cache.get_json(redis, key) == {"value": 1}
    await asyncio.sleep(0.5)
    assert await cache.get_json(redis, key) == {"value": 1}
    await asyncio.sleep(1.2)
    assert await cache.get_json(redis, key) is None


@pytest.mark.asyncio
async def test_get_json_handles_errors():
    class BrokenRedis:
        async def get(self, key):
            raise RuntimeError("boom")

    class InvalidRedis:
        async def get(self, key):
            return "not-json"

    assert await cache.get_json(BrokenRedis(), "key") is None
    assert await cache.get_json(InvalidRedis(), "key") is None


@pytest.mark.asyncio
async def test_set_json_handles_invalid_payload():
    redis = FakeRedis()
    assert not await cache.set_json(redis, "stats:key", object(), ttl_s=5)

    class BrokenRedis(FakeRedis):
        async def set(self, *_args, **_kwargs):
            raise RuntimeError("fail")

    assert not await cache.set_json(BrokenRedis(), "stats:key", {"ok": True}, ttl_s=5)
    assert not await cache.set_json(redis, "stats:key", {"ok": True}, ttl_s=0)


@pytest.mark.asyncio
async def test_set_returns_metadata_records_window():
    redis = FakeRedis()
    await cache.set_returns_metadata(
        redis,
        "stats:returns:test",
        date_from=None,
        date_to=None,
        ttl_s=5,
    )
    meta_key = cache.returns_metadata_key("stats:returns:test")
    assert await cache.get_json(redis, meta_key) == {"date_from": None, "date_to": None}


@pytest.mark.asyncio
async def test_purge_prefix_and_returns_cache():
    redis = FakeRedis()
    await redis.set("stats:kpi:1", "{}", ex=5)
    await redis.set("stats:kpi:2", "{}", ex=5)
    deleted = await cache.purge_prefix(redis, "stats:kpi")
    assert deleted == 2
    await redis.set("stats:returns:hit", "{}", ex=5)
    await redis.set(
        "stats:returns:hit:meta",
        json.dumps({"date_from": "2024-01-01", "date_to": "2024-01-07"}),
        ex=5,
    )
    await redis.set("stats:returns:miss", "{}", ex=5)
    await redis.set(
        "stats:returns:miss:meta",
        json.dumps({"date_from": "2023-01-01", "date_to": "2023-01-02"}),
        ex=5,
    )
    deleted = await cache.purge_returns_cache(
        redis,
        "stats:",
        date_from=None,
        date_to=None,
    )
    assert deleted >= 2
    await redis.set("stats:returns:all", "{}", ex=5)
    await redis.set(
        "stats:returns:all:meta",
        json.dumps({"date_from": "2024-01-02", "date_to": "2024-01-05"}),
        ex=5,
    )
    deleted = await cache.purge_returns_cache(
        redis,
        "stats:",
        date_from=cache.dt.date(2024, 1, 1),
        date_to=cache.dt.date(2024, 1, 10),
    )
    assert deleted >= 2


def test_meta_overlap_helpers():
    window_start = cache.dt.date(2024, 1, 1)
    window_end = cache.dt.date(2024, 1, 10)
    assert cache._meta_overlaps({"date_from": "2024-01-02", "date_to": "2024-01-03"}, window_start, window_end)
    assert not cache._meta_overlaps({"date_from": "2023-01-01", "date_to": "2023-01-05"}, window_start, window_end)
