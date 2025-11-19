from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException, Request
from fastapi_limiter import FastAPILimiter
from starlette.datastructures import Headers
from starlette.routing import Match

from awa_common.security.models import Role, UserCtx
from awa_common.settings import settings
from services.api import rate_limit
from tests.fakes import FakeRedis

pytestmark = pytest.mark.anyio


def _make_request(path: str = "/score", method: str = "GET", ip: str = "127.0.0.1") -> Request:
    scope = {
        "type": "http",
        "path": path,
        "method": method,
        "headers": Headers({}).raw,
        "client": (ip, 1234),
        "scheme": "http",
        "server": ("test", 80),
        "query_string": b"",
        "app": None,
        "router": None,
        "route": SimpleNamespace(path=path, methods=[method], name=path, match=Match.FULL),
    }
    request = Request(scope)
    return request


@pytest.fixture(autouse=True)
def _fake_redis(monkeypatch: pytest.MonkeyPatch):
    FastAPILimiter.redis = FakeRedis()
    yield
    FastAPILimiter.redis = None


def _test_user() -> UserCtx:
    return UserCtx(
        sub="user-1",
        email="user@example.com",
        roles=[Role.viewer],
        raw_claims={"iss": settings.OIDC_ISSUER},
    )


async def test_build_rate_key_authenticated():
    request = _make_request("/stats/roi")
    user = _test_user()
    key = rate_limit.build_rate_key(request, user)
    assert key.startswith("awa")
    assert "user-1" in key
    assert "/stats/roi" in key


async def test_build_rate_key_unauthenticated():
    request = _make_request("/health", ip="10.0.0.10")
    key = rate_limit.build_rate_key(request, None)
    assert key.startswith("public")
    assert "10.0.0.10" in key
    assert "anon" in key


async def test_role_based_limit_enforced(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_VIEWER", "1/second")
    limiter = rate_limit.SmartRateLimiter(settings)
    dependency = limiter.dependency()

    request = _make_request("/score")
    request.state.user = _test_user()

    await dependency(request)
    with pytest.raises(HTTPException) as excinfo:
        await dependency(request)
    assert excinfo.value.headers["Retry-After"] == "1"


async def test_score_profile_overrides_viewer_limit(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_VIEWER", "5/second")
    monkeypatch.setattr(settings, "RATE_LIMIT_SCORE_PER_USER", 1)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)
    dependency = rate_limit.score_rate_limiter()

    request = _make_request("/score")
    request.state.user = _test_user()

    await dependency(request)
    with pytest.raises(HTTPException) as excinfo:
        await dependency(request)
    headers = excinfo.value.headers
    retry_after = int(headers["Retry-After"])
    assert 0 < retry_after <= 60
    assert headers["X-RateLimit-Limit"] == "1"


async def test_rate_limiter_uses_token_when_available(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, Any] = {}

    async def _fake_validate(token: str, *, cfg=None):
        captured["token"] = token
        return _test_user()

    monkeypatch.setattr(rate_limit.oidc, "validate_access_token", _fake_validate, raising=True)
    limiter = rate_limit.SmartRateLimiter(settings)
    dependency = limiter.dependency()
    request = _make_request("/stats/roi")
    request.scope["headers"] = Headers({"Authorization": "Bearer test-token"}).raw

    await dependency(request)
    assert captured["token"] == "test-token"


@pytest.mark.anyio
async def test_rate_limit_allows_when_redis_errors(monkeypatch: pytest.MonkeyPatch):
    class BrokenRedis(FakeRedis):
        async def incr(self, key):
            raise RuntimeError("redis down")

    FastAPILimiter.redis = BrokenRedis()
    limiter = rate_limit.SmartRateLimiter(settings)
    dependency = limiter.dependency()
    request = _make_request("/score")
    request.state.user = _test_user()
    metrics_calls = {"count": 0}
    error_calls = {"count": 0}
    sentry_calls = {"count": 0}

    def _record(*args, **kwargs):
        metrics_calls["count"] += 1

    class DummyLogger:
        def error(self, *args, **kwargs):
            error_calls["count"] += 1

        def warning(self, *args, **kwargs):
            pass

    def _capture(exc):
        sentry_calls["count"] += 1

    monkeypatch.setattr(rate_limit, "record_redis_error", _record)
    monkeypatch.setattr(rate_limit, "logger", DummyLogger())
    monkeypatch.setattr(rate_limit.sentry_sdk, "capture_exception", _capture)

    await dependency(request)
    assert metrics_calls["count"] == 1
    assert error_calls["count"] == 1
    assert sentry_calls["count"] == 1
