from services.common.db_url import build_url


def test_build_url_from_parts(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("PG_SYNC_DSN", raising=False)
    monkeypatch.delenv("PG_ASYNC_DSN", raising=False)
    monkeypatch.setenv("PG_USER", "u")
    monkeypatch.setenv("PG_PASSWORD", "p")
    monkeypatch.setenv("PG_HOST", "h")
    monkeypatch.setenv("PG_PORT", "1")
    monkeypatch.setenv("PG_DATABASE", "d")
    assert build_url() == "postgresql+asyncpg://u:p@h:1/d"
    assert build_url(async_=False) == "postgresql+psycopg://u:p@h:1/d"


def test_build_url_toggles_database_url(monkeypatch):
    monkeypatch.delenv("PG_SYNC_DSN", raising=False)
    monkeypatch.delenv("PG_ASYNC_DSN", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h:1/d")
    assert build_url() == "postgresql+asyncpg://u:p@h:1/d"
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:1/d")
    assert build_url(async_=False) == "postgresql+psycopg://u:p@h:1/d"
