import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from services.api.routes import health
from tests.unit.conftest import _StubResult


def _make_request(state: SimpleNamespace | None = None) -> SimpleNamespace:
    if state is None:
        state = SimpleNamespace(
            stats_cache=None,
            redis_health={"critical": False, "status": "unknown", "error": None},
            redis_url=None,
        )
    return SimpleNamespace(app=SimpleNamespace(state=state))


@pytest.mark.asyncio
async def test_health_ok(fake_db_session):
    now = datetime.now(UTC)
    session = fake_db_session(_StubResult(scalar=now))
    response = await health.health(request=_make_request(), session=session)
    assert response.status_code == 200
    assert response.body and b"ok" in response.body


@pytest.mark.asyncio
async def test_health_clock_skew(fake_db_session):
    old = datetime.now(UTC) - timedelta(minutes=5)
    session = fake_db_session(_StubResult(scalar=old))
    response = await health.health(request=_make_request(), session=session)
    assert response.status_code == 503
    assert b"clock_skew" in response.body


@pytest.mark.asyncio
async def test_health_includes_redis_snapshot(monkeypatch, fake_db_session):
    session = fake_db_session(_StubResult(scalar=datetime.now(UTC)))

    class BrokenRedis:
        async def ping(self):
            raise RuntimeError("redis down")

    state = SimpleNamespace(
        stats_cache=BrokenRedis(),
        redis_health={"critical": False, "status": "unknown", "error": None},
    )
    request = _make_request(state)
    monkeypatch.setattr(health.FastAPILimiter, "redis", None, raising=False)
    metrics = {"count": 0}
    monkeypatch.setattr(
        health, "record_redis_error", lambda *args, **kwargs: metrics.__setitem__("count", metrics["count"] + 1)
    )
    monkeypatch.setattr(health.sentry_sdk, "capture_exception", lambda exc: None)
    response = await health.health(session=session, request=request)
    assert response.status_code == 200
    payload = json.loads(response.body)
    assert payload["redis"]["status"] == "degraded"
    assert metrics["count"] == 1


@pytest.mark.asyncio
async def test_health_fails_when_redis_critical(monkeypatch, fake_db_session):
    session = fake_db_session(_StubResult(scalar=datetime.now(UTC)))

    class BrokenRedis:
        async def ping(self):
            raise RuntimeError("redis down")

    state = SimpleNamespace(
        stats_cache=BrokenRedis(),
        redis_health={"critical": True, "status": "unknown", "error": None},
    )
    request = _make_request(state)
    monkeypatch.setattr(health.FastAPILimiter, "redis", None, raising=False)
    monkeypatch.setattr(health, "record_redis_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(health.sentry_sdk, "capture_exception", lambda exc: None)
    response = await health.health(session=session, request=request)
    assert response.status_code == 503
    payload = json.loads(response.body)
    assert payload["detail"] == "redis_unavailable"


@pytest.mark.asyncio
async def test_health_reports_degraded_when_some_clients_fail(monkeypatch, fake_db_session):
    session = fake_db_session(_StubResult(scalar=datetime.now(UTC)))

    class GoodRedis:
        async def ping(self):
            return True

    class BrokenRedis:
        async def ping(self):
            raise RuntimeError("redis down")

    state = SimpleNamespace(
        stats_cache=GoodRedis(),
        redis_health={"critical": False, "status": "unknown", "error": None},
        limiter_redis=BrokenRedis(),
    )
    request = _make_request(state)
    monkeypatch.setattr(health.FastAPILimiter, "redis", BrokenRedis(), raising=False)
    monkeypatch.setattr(health, "record_redis_error", lambda *args, **kwargs: None)
    monkeypatch.setattr(health.sentry_sdk, "capture_exception", lambda exc: None)
    response = await health.health(session=session, request=request)
    assert response.status_code == 200
    payload = json.loads(response.body)
    assert payload["redis"]["status"] == "degraded"
