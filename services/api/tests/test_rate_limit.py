import os

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

# Set env BEFORE importing app so the limiter initializes properly in this process.
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RATE_LIMIT_DEFAULT", "100/minute")  # high enough to avoid interference
os.environ.setdefault("TRUST_X_FORWARDED", "1")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:pass@localhost:5432/awa")

from services.api import db as api_db  # noqa: E402
from services.api import main as api_main  # noqa: E402


async def _noop() -> None:
    pass


@pytest.fixture(autouse=True)
def _stub_wait_for_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_main, "_wait_for_db", _noop)


app = api_main.app  # noqa: E402


class FakeSession:
    async def execute(self, query):
        class R:
            def scalar(self):
                from datetime import UTC, datetime

                return datetime.now(UTC)

        return R()


async def fake_get_session():
    yield FakeSession()


def test_rate_limit_exceeded_returns_429():
    # Use a unique client IP so we don't affect other tests.
    headers = {"X-Forwarded-For": "203.0.113.77"}
    with TestClient(app) as client:
        app.dependency_overrides[api_db.get_session] = fake_get_session
        try:
            # exceed 100/min quickly (send >100 GETs)
            codes = []
            for _ in range(120):
                r = client.get("/health", headers=headers)
                codes.append(r.status_code)
            counts = {code: codes.count(code) for code in set(codes)}
            assert 429 in codes, f"No 429 observed, got counts: {counts}"
        finally:
            app.dependency_overrides.clear()


def test_different_client_ip_has_independent_bucket():
    with TestClient(app) as client:
        app.dependency_overrides[api_db.get_session] = fake_get_session
        try:
            r1 = client.get("/health", headers={"X-Forwarded-For": "203.0.113.88"})
            r2 = client.get("/health", headers={"X-Forwarded-For": "203.0.113.99"})
            assert r1.status_code == 200 and r2.status_code == 200
        finally:
            app.dependency_overrides.clear()
