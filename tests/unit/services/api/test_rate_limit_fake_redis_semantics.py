from __future__ import annotations

import pytest

from awa_common.settings import settings
from services.api import rate_limit
from tests.fakes import FakeRedis

pytestmark = pytest.mark.anyio


async def test_fake_redis_ttl_and_reset(monkeypatch: pytest.MonkeyPatch):
    redis = FakeRedis()
    current = {"value": 100.0}

    def _now() -> float:
        return current["value"]

    monkeypatch.setattr(redis, "_now", _now, raising=False)
    limiter = rate_limit.SmartRateLimiter(settings)

    allowed, remaining, reset = await limiter._consume(redis, "bucket", limit=2, window=5)
    assert allowed is True
    assert remaining == 1
    assert reset == 5

    allowed, remaining, reset = await limiter._consume(redis, "bucket", limit=2, window=5)
    assert allowed is True
    assert remaining == 0
    assert reset == 5

    allowed, remaining, reset = await limiter._consume(redis, "bucket", limit=2, window=5)
    assert allowed is False
    assert remaining == 0
    assert reset == 5

    current["value"] += 6
    allowed, remaining, reset = await limiter._consume(redis, "bucket", limit=2, window=5)
    assert allowed is True
    assert remaining == 1
    assert reset == 5
