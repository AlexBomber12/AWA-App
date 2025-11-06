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
