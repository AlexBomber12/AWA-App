import pytest

from services.worker import ready as ready_module


@pytest.mark.asyncio
async def test_ready_success(mock_redis_ping, mock_celery_inspect):
    resp = await ready_module.ready()
    assert resp["status"] == "ok"


@pytest.mark.asyncio
async def test_ready_redis_failure(monkeypatch):
    class DummyRedis:
        def ping(self):
            raise RuntimeError("redis down")

    monkeypatch.setattr(ready_module.redis, "from_url", lambda *_: DummyRedis())
    body, status = await ready_module.ready()
    assert status == ready_module.status.HTTP_503_SERVICE_UNAVAILABLE
    assert body["reason"] == "redis"


@pytest.mark.asyncio
async def test_ready_celery_failure(mock_redis_ping, monkeypatch):
    class DummyInspect:
        def ping(self):
            return {}

    class DummyControl:
        def inspect(self, timeout=1):
            return DummyInspect()

    class DummyCelery:
        def __init__(self):
            self.control = DummyControl()

    monkeypatch.setattr(ready_module, "celery_app", DummyCelery())
    body, status = await ready_module.ready()
    assert status == ready_module.status.HTTP_503_SERVICE_UNAVAILABLE
    assert body["reason"] == "celery-ping"
