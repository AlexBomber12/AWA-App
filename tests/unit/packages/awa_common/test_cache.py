from __future__ import annotations

import asyncio

import pytest

from awa_common.cache import build_cache_key, get_json, set_json
from tests.fakes import FakeRedis


def test_stats_cache_key_stability():
    namespace = "stats:"
    params_a = {"vendor": "Acme", "date_from": "2024-01-01"}
    params_b = [("date_from", "2024-01-01"), ("vendor", "Acme")]
    key_a = build_cache_key(namespace, "returns", params_a)
    key_b = build_cache_key(namespace, "returns", list(reversed(params_b)))
    assert key_a == key_b

    key_c = build_cache_key(namespace, "returns", {"vendor": "Other"})
    assert key_c != key_a


@pytest.mark.asyncio
@pytest.mark.real_sleep
async def test_stats_cache_ttl():
    redis = FakeRedis()
    key = build_cache_key("stats:", "kpi", None)
    assert await set_json(redis, key, {"value": 1}, ttl_s=1)

    cached = await get_json(redis, key)
    assert cached == {"value": 1}

    await asyncio.sleep(0.5)
    assert await get_json(redis, key) == {"value": 1}

    await asyncio.sleep(1.2)
    assert await get_json(redis, key) is None
