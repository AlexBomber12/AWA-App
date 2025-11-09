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


def test_celery_broker_alias(monkeypatch) -> None:
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    settings = Settings()
    assert settings.BROKER_URL == "memory://"


def test_new_logistics_and_http_fields(monkeypatch) -> None:
    monkeypatch.setenv("ETL_HTTP_MAX_CONNECTIONS", "32")
    monkeypatch.setenv("LOGISTICS_TIMEOUT_S", "21")
    monkeypatch.setenv("FREIGHT_API_URL", "https://example.com/rates.csv")
    settings = Settings()
    assert settings.ETL_HTTP_MAX_CONNECTIONS == 32
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
