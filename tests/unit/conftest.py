import asyncio
from collections import deque
from typing import Any, AsyncIterator, Iterable

import httpx
import pytest
from httpx import ASGITransport

from tests.fakes import FakeRedis


class _StubResult:
    def __init__(
        self,
        *,
        scalar: Any = None,
        mappings: Iterable[dict[str, Any]] | None = None,
        rowcount: int = 0,
    ):
        self._scalar = scalar
        self._rows = list(mappings or [])
        self.rowcount = rowcount

    def scalar(self) -> Any:
        return self._scalar

    def scalars(self) -> "_StubResult":
        return self

    def mappings(self) -> "_StubResult":
        return self

    def all(self) -> list[dict[str, Any]]:
        return list(self._rows)

    def first(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None


class _StubSession:
    def __init__(self, *results: _StubResult):
        self._queue: deque[_StubResult] = deque(results)
        self.executed: list[tuple[Any, Any]] = []
        self.committed = False

    async def execute(self, stmt: Any, params: Any | None = None) -> _StubResult:
        self.executed.append((stmt, params))
        if self._queue:
            return self._queue.popleft()
        return _StubResult()

    async def commit(self) -> None:
        self.committed = True


@pytest.fixture(scope="session")
def event_loop() -> AsyncIterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


@pytest.fixture(autouse=True)
def _patch_wait_for_db_autouse(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    """Provide a fast no-op wait_for_db unless a test opts out via marker."""

    if request.node.get_closest_marker("needs_wait_for_db"):
        return

    import services.api.main as api_main

    async def _fake_wait_for_db() -> None:
        return None

    monkeypatch.setattr(api_main, "_wait_for_db", _fake_wait_for_db)


@pytest.fixture(autouse=True)
def settings_env(monkeypatch: pytest.MonkeyPatch):
    """Set safe defaults for all tests and update shared settings instance."""

    from awa_common import settings as settings_module

    overrides = {
        "ENV": "test",
        "APP_NAME": "awa-test",
        "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/app",
        "REDIS_URL": "redis://localhost:6379/0",
        "LOG_LEVEL": "INFO",
        "SENTRY_DSN": "",
        "NEXT_PUBLIC_API_URL": "http://localhost:8000",
        "REQUEST_TIMEOUT_S": 5,
        "LLM_PROVIDER": "STUB",
        "LLM_PROVIDER_FALLBACK": "STUB",
        "OPENAI_API_BASE": "",
        "OPENAI_API_KEY": "",
    }

    for key, value in overrides.items():
        monkeypatch.setenv(key, str(value))

    settings = settings_module.settings
    for key, value in overrides.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    monkeypatch.setenv("TESTING", "1")
    return settings


@pytest.fixture
def api_app(settings_env, monkeypatch: pytest.MonkeyPatch):  # noqa: ANN001
    """Return the FastAPI application with external dependencies stubbed."""
    import services.api.main as api_main

    class DummyRedis:
        def __init__(self, url: str):
            self.url = url
            self.pings = 0

        async def ping(self) -> str:
            self.pings += 1
            return "PONG"

    async def _fake_wait_for_redis(url: str):
        return DummyRedis(url)

    async def _fake_check_llm() -> None:
        return None

    monkeypatch.setattr(api_main, "_wait_for_redis", _fake_wait_for_redis)
    monkeypatch.setattr(api_main, "_check_llm", _fake_check_llm)

    class DummyLimiter:
        redis: Any | None = FakeRedis()
        closed = False

        @staticmethod
        async def init(redis_client: Any) -> None:
            DummyLimiter.redis = redis_client

        @staticmethod
        async def close() -> None:
            DummyLimiter.closed = True

    class DummyRateLimiter:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        async def __call__(self, request, response) -> None:  # noqa: ANN001
            request.state.rate_limited = True

    monkeypatch.setattr(api_main, "FastAPILimiter", DummyLimiter)
    monkeypatch.setattr(api_main, "RateLimiter", DummyRateLimiter)

    return api_main.app


@pytest.fixture
async def api_client(api_app):
    """HTTPX client backed by the FastAPI app."""
    transport = ASGITransport(app=api_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def fake_db_session():
    """Factory returning an async session stub with queued results."""

    def factory(*results: _StubResult) -> _StubSession:
        return _StubSession(*results)

    return factory


@pytest.fixture
def mock_redis_ping(monkeypatch: pytest.MonkeyPatch):
    """Patch redis.from_url used by worker ready probe."""
    import services.worker.ready as ready_mod

    class DummyRedis:
        def __init__(self):
            self.pings = 0

        def ping(self) -> None:
            self.pings += 1

    dummy = DummyRedis()

    def _from_url(_url: str, *args, **kwargs):
        return dummy

    monkeypatch.setattr(ready_mod.redis, "from_url", _from_url)
    return dummy


@pytest.fixture
def mock_celery_inspect(monkeypatch: pytest.MonkeyPatch):
    """Patch celery inspect used by worker ready probe."""
    import services.worker.ready as ready_mod

    class DummyInspect:
        def __init__(self):
            self.calls = 0

        def ping(self):
            self.calls += 1
            return {"worker@local": "pong"}

    class DummyControl:
        def __init__(self):
            self.inspect_calls: list[int] = []
            self.inspect_obj = DummyInspect()

        def inspect(self, timeout: int = 1):
            self.inspect_calls.append(timeout)
            return self.inspect_obj

    class DummyCelery:
        def __init__(self):
            self.control = DummyControl()

    dummy = DummyCelery()
    monkeypatch.setattr(ready_mod, "celery_app", dummy)
    return dummy


__all__ = [
    "_StubResult",
    "_StubSession",
    "api_app",
    "api_client",
    "fake_db_session",
    "mock_celery_inspect",
    "mock_redis_ping",
    "settings_env",
]
