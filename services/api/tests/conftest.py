import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

pytest_plugins = ("tests.conftest",)


@pytest.fixture(autouse=True)
def _api_fast_startup(monkeypatch, request):
    """
    Neutralize blocking startup for API tests that construct TestClient(main.app):
    - fastapi_limiter FastAPILimiter.init/close no-op
    - redis.asyncio.from_url returns a fake client with ping/aclose
    - services.api.main._wait_for_db no-op unless @pytest.mark.needs_wait_for_db
    """
    if request.node.get_closest_marker("real_lifespan"):
        return
    try:
        import fastapi_limiter

        async def _noop_async(*_a, **_k):
            return None

        class _FakeLimiterRedis:
            async def evalsha(self, *_a, **_k):
                return 0

            async def script_load(self, *_a, **_k):
                return "noop"

        monkeypatch.setattr(fastapi_limiter.FastAPILimiter, "init", _noop_async, raising=True)
        monkeypatch.setattr(fastapi_limiter.FastAPILimiter, "close", _noop_async, raising=False)
        monkeypatch.setattr(
            fastapi_limiter.FastAPILimiter, "redis", _FakeLimiterRedis(), raising=False
        )
        monkeypatch.setattr(fastapi_limiter.FastAPILimiter, "lua_sha", "noop", raising=False)
    except Exception:
        pass

    try:
        import redis.asyncio as aioredis

        class _FakeRedis:
            async def ping(self):
                return True

            async def aclose(self):
                return None

        monkeypatch.setattr(aioredis, "from_url", lambda *_a, **_k: _FakeRedis(), raising=True)
    except Exception:
        pass

    if not request.node.get_closest_marker("needs_wait_for_db"):
        try:
            import services.api.main as main

            async def _noop_wait():
                return None

            monkeypatch.setattr(main, "_wait_for_db", _noop_wait, raising=True)
        except Exception:
            pass
