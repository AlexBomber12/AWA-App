from __future__ import annotations

import pytest

try:
    from fastapi_limiter import FastAPILimiter
except Exception:  # pragma: no cover - fastapi-limiter optional in some envs
    FastAPILimiter = None  # type: ignore


@pytest.mark.unit
def test_fastapi_limiter_fake_is_installed():
    if FastAPILimiter is None:
        pytest.skip("fastapi-limiter not installed")
    redis = getattr(FastAPILimiter, "redis", None)
    assert hasattr(redis, "evalsha"), "Expected fake Redis with evalsha for unit tests"
    assert FastAPILimiter.lua_sha, "Expected fake lua_sha to be non-empty"
