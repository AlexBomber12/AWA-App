import pytest

import awa_common.settings as settings_module
from awa_common.settings import Settings


def test_settings_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:secret@db/app")
    settings = Settings()
    assert settings.ENV == "prod"
    assert settings.DATABASE_URL.endswith("@db/app")


def test_redacted_masks_credentials() -> None:
    settings = Settings(DATABASE_URL="postgresql+psycopg://user:secret@db/app")
    redacted = settings.redacted()
    assert redacted["DATABASE_URL"] == "postgresql+psycopg://user:****@db/app"


def test_celery_broker_alias(monkeypatch, caplog: pytest.LogCaptureFixture) -> None:
    settings_module._LEGACY_LOGGED.clear()
    settings_module._LEGACY_ENV_USED.clear()
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    cfg = Settings()
    assert cfg.BROKER_URL == "memory://"
    assert ("CELERY_BROKER_URL", "BROKER_URL") in settings_module._LEGACY_ENV_USED
    assert any("config.legacy_env_alias" in rec.message for rec in caplog.records)


def test_new_logistics_and_http_fields(monkeypatch) -> None:
    monkeypatch.setenv("HTTP_MAX_CONNECTIONS", "32")
    monkeypatch.setenv("LOGISTICS_TIMEOUT_S", "21")
    monkeypatch.setenv("FREIGHT_API_URL", "https://example.com/rates.csv")
    settings = Settings()
    assert settings.HTTP_MAX_CONNECTIONS == 32
    assert settings.LOGISTICS_TIMEOUT_S == 21
    assert settings.FREIGHT_API_URL == "https://example.com/rates.csv"


def test_ensure_asyncpg_dsn_converts_postgres(monkeypatch) -> None:
    from awa_common.settings import _ensure_asyncpg_dsn

    value = _ensure_asyncpg_dsn("postgresql://user:pass@host/app")
    assert value.startswith("postgresql+asyncpg://")
    assert _ensure_asyncpg_dsn("mysql://host/app") == "mysql://host/app"


def test_postgres_dsn_uses_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://env-user@db/app")
    cfg = Settings()
    assert cfg.POSTGRES_DSN.startswith("postgresql+asyncpg://env-user")


def test_postgres_dsn_falls_back_to_database_url(monkeypatch) -> None:
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.delenv("PG_ASYNC_DSN", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://fallback@db/app")
    cfg = Settings(PG_ASYNC_DSN=None)
    assert cfg.POSTGRES_DSN.startswith("postgresql+asyncpg://fallback")


def test_healthcheck_settings(monkeypatch) -> None:
    monkeypatch.setenv("HEALTHCHECK_DB_TIMEOUT_S", "5")
    monkeypatch.setenv("HEALTHCHECK_REDIS_SOCKET_TIMEOUT_S", "4")
    monkeypatch.setenv("HEALTHCHECK_HTTP_TIMEOUT_S", "6")
    monkeypatch.setenv("HEALTHCHECK_CELERY_TIMEOUT_S", "7")
    monkeypatch.setenv("HEALTHCHECK_INSPECT_TIMEOUT_S", "8")
    monkeypatch.setenv("HEALTHCHECK_RETRY_ATTEMPTS", "9")
    monkeypatch.setenv("HEALTHCHECK_RETRY_DELAY_S", "0.5")
    cfg = Settings()
    assert cfg.HEALTHCHECK_DB_TIMEOUT_S == 5.0
    assert cfg.HEALTHCHECK_REDIS_SOCKET_TIMEOUT_S == 4.0
    assert cfg.HEALTHCHECK_HTTP_TIMEOUT_S == 6.0
    assert cfg.HEALTHCHECK_CELERY_TIMEOUT_S == 7.0
    assert cfg.HEALTHCHECK_INSPECT_TIMEOUT_S == 8.0
    assert cfg.HEALTHCHECK_RETRY_ATTEMPTS == 9
    assert cfg.HEALTHCHECK_RETRY_DELAY_S == 0.5
