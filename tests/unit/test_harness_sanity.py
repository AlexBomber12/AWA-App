from __future__ import annotations

import pytest


@pytest.mark.unit
def test_rate_limiter_and_audit_harness_is_installed() -> None:
    from fastapi_limiter import FastAPILimiter

    redis_client = getattr(FastAPILimiter, "redis", None)
    assert hasattr(redis_client, "evalsha"), "FakeRedis not installed; FastAPILimiter.redis lacks evalsha"
    assert FastAPILimiter.lua_sha, "FastAPILimiter.lua_sha must be non-empty for unit harness"

    import services.api.audit as audit

    assert callable(getattr(audit, "insert_audit", None)), "Strict audit spy is not installed"
