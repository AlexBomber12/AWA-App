import os

from awa_common import settings as settings_module
from awa_common.settings import Settings, _default_env_file


def test_default_env_file_local_prefers_env_local(tmp_path, monkeypatch):
    monkeypatch.setenv("ENV", "local")
    env_local = tmp_path / ".env.local"
    env_local.write_text("DATABASE_URL=postgresql://example\n", encoding="utf-8")
    monkeypatch.setattr(os.path, "exists", lambda p: p == ".env.local")
    assert _default_env_file() == ".env.local"


def test_default_env_file_test_without_file(monkeypatch):
    monkeypatch.setenv("ENV", "test")

    def fake_exists(_path: str) -> bool:
        return False

    monkeypatch.setattr(os.path, "exists", fake_exists)
    assert _default_env_file() is None


def test_settings_redacted_masks_credentials(monkeypatch):
    settings = Settings(
        DATABASE_URL="postgresql+psycopg://user:secret@db:5432/app",
        REDIS_URL="redis://user:other@localhost:6379/0",
        OPENAI_API_BASE="https://api.openai.com",
        OPENAI_API_KEY="sk-secret",
    )
    redacted = settings.redacted()
    assert "secret" not in str(redacted)
    assert redacted["DATABASE_URL"].endswith("@db:5432/app")
    assert redacted["REDIS_URL"].endswith("@localhost:6379/0")
    assert redacted["SENTRY_DSN"] is None
    assert redacted["OPENAI_API_BASE"] is True
    assert redacted["OPENAI_API_KEY"] is True


def test_settings_fixture_overrides_environment(settings_env):
    assert settings_module.settings.ENV == "test"
    assert settings_module.settings.APP_NAME == "awa-test"
