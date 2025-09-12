from packages.awa_common.settings import Settings


def test_defaults_local_envfile_resolution(monkeypatch, tmp_path):
    env_file = tmp_path / ".env.local"
    env_file.write_text("DATABASE_URL=postgresql+psycopg://u:p@db:5432/app\n")
    monkeypatch.chdir(tmp_path)
    s = Settings()
    assert s.DATABASE_URL.endswith("@db:5432/app")


def test_validation_and_types(monkeypatch):
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db:5432/app")
    s = Settings()
    assert s.ENV == "test"
    assert s.DATABASE_URL.startswith("postgresql+psycopg://")


def test_redaction():
    s = Settings(DATABASE_URL="postgresql+psycopg://u:secret@db/app")
    red = s.redacted()
    assert "secret" not in str(red)
