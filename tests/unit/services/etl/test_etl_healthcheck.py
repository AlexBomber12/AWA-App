import types

from services.etl import healthcheck


def test_db_timeout_respects_setting(monkeypatch):
    monkeypatch.setattr(healthcheck.settings, "HEALTHCHECK_DB_TIMEOUT_S", 4.2, raising=False)
    assert healthcheck._db_timeout() == 4.2


def test_http_timeout_respects_setting(monkeypatch):
    monkeypatch.setattr(healthcheck.settings, "HEALTHCHECK_HTTP_TIMEOUT_S", 9.5, raising=False)
    assert healthcheck._http_timeout() == 9.5


def test_check_db_uses_psycopg_timeout(monkeypatch):
    class DummyCursor:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def execute(self, _sql):
            self.executed = True

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def cursor(self):
            return DummyCursor()

    captured = {}

    def fake_connect(dsn, connect_timeout):
        captured["dsn"] = dsn
        captured["timeout"] = connect_timeout
        return DummyConn()

    monkeypatch.setattr(healthcheck, "psycopg", types.SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(healthcheck.settings, "HEALTHCHECK_DB_TIMEOUT_S", 3.3, raising=False)
    healthcheck.check_db()
    assert captured["timeout"] == 3.3


def test_check_minio_hits_health_endpoint(monkeypatch):
    requests = {}

    def fake_urlopen(req, timeout):
        requests["url"] = req.full_url
        requests["timeout"] = timeout

    s3_cfg = types.SimpleNamespace(endpoint="minio:9000", secure=False, region="us-east-1")
    monkeypatch.setattr(healthcheck, "settings", types.SimpleNamespace(s3=s3_cfg))
    monkeypatch.setattr(healthcheck, "urlopen", fake_urlopen)
    monkeypatch.setattr(healthcheck, "_http_timeout", lambda: 5.0)
    healthcheck.check_minio()
    assert requests["url"].endswith("/minio/health/ready")
    assert requests["timeout"] == 5.0
