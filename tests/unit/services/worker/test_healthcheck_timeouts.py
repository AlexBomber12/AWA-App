import types

from services.worker import healthcheck


def test_worker_timeout_helpers(monkeypatch):
    monkeypatch.setattr(healthcheck.settings, "HEALTHCHECK_DB_TIMEOUT_S", 7.7, raising=False)
    monkeypatch.setattr(healthcheck.settings, "HEALTHCHECK_REDIS_SOCKET_TIMEOUT_S", 6.6, raising=False)
    monkeypatch.setattr(healthcheck.settings, "HEALTHCHECK_CELERY_TIMEOUT_S", 5.5, raising=False)
    assert healthcheck._db_timeout() == 7.7
    assert healthcheck._redis_timeout() == 6.6
    assert healthcheck._celery_timeout() == 5.5


def test_check_db_invokes_psycopg_with_timeout(monkeypatch):
    captured = {}

    class DummyCursor:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def execute(self, _sql):
            captured["executed"] = True

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def cursor(self):
            return DummyCursor()

    def fake_connect(dsn, connect_timeout):
        captured["dsn"] = dsn
        captured["timeout"] = connect_timeout
        return DummyConn()

    monkeypatch.setattr(healthcheck, "psycopg", types.SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(healthcheck.settings, "HEALTHCHECK_DB_TIMEOUT_S", 4.4, raising=False)
    healthcheck.check_db()
    assert captured["timeout"] == 4.4
    assert captured["executed"] is True


def test_check_redis_uses_configured_timeout(monkeypatch):
    recorded = {}

    class DummyRedis:
        def __init__(self, url, **kwargs):
            recorded["url"] = url
            recorded.update(kwargs)

        def ping(self):
            recorded["pinged"] = True

        @classmethod
        def from_url(cls, url, **kwargs):
            return cls(url, **kwargs)

    monkeypatch.setattr(healthcheck, "redis", types.SimpleNamespace(Redis=DummyRedis))
    monkeypatch.setattr(healthcheck.settings, "HEALTHCHECK_REDIS_SOCKET_TIMEOUT_S", 1.5, raising=False)
    healthcheck.check_redis()
    assert recorded["socket_timeout"] == 1.5
    assert recorded["pinged"] is True


def test_ping_worker_uses_configured_timeout(monkeypatch):
    captured = {}

    class DummyControl:
        def ping(self, timeout):
            captured["timeout"] = timeout
            return True

    class DummyApp:
        control = DummyControl()

    monkeypatch.setattr(healthcheck, "celery_app", DummyApp())
    monkeypatch.setattr(healthcheck.settings, "HEALTHCHECK_CELERY_TIMEOUT_S", 2.5, raising=False)
    healthcheck.ping_worker()
    assert captured["timeout"] == 2.5
