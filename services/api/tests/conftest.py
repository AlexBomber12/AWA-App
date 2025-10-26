import pytest


@pytest.fixture(autouse=True)
def _api_fast_startup(monkeypatch):
    """
    Neutralize blocking startup for API tests that construct TestClient(main.app):
    - fastapi_limiter FastAPILimiter.init/close no-op
    - redis.asyncio.from_url returns a fake client with ping/aclose
    - services.api.main._wait_for_db no-op
    """
    try:
        import fastapi_limiter

        async def _noop_async(*_a, **_k):
            return None

        monkeypatch.setattr(
            fastapi_limiter.FastAPILimiter, "init", _noop_async, raising=True
        )
        monkeypatch.setattr(
            fastapi_limiter.FastAPILimiter, "close", _noop_async, raising=False
        )
    except Exception:
        pass

    try:
        import redis.asyncio as aioredis

        class _FakeRedis:
            async def ping(self):
                return True

            async def aclose(self):
                return None

        monkeypatch.setattr(
            aioredis, "from_url", lambda *_a, **_k: _FakeRedis(), raising=True
        )
    except Exception:
        pass

    try:
        import services.api.main as main

        async def _noop_wait():
            return None

        monkeypatch.setattr(main, "_wait_for_db", _noop_wait, raising=True)
    except Exception:
        pass
