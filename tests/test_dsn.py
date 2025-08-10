import os

from services.common.dsn import build_dsn


def test_build_dsn_sync_suffix():
    os.environ.pop("DATABASE_URL", None)
    dsn = build_dsn(sync=True)
    assert "+psycopg" in dsn


def test_build_dsn_default_host_postgres(monkeypatch):
    # Clear all database URLs first to force build_dsn to use PG_* vars
    for key in ["DATABASE_URL", "PG_SYNC_DSN", "PG_ASYNC_DSN"]:
        monkeypatch.delenv(key, raising=False)

    # Set the specific PG_* variables to test the expected behavior
    monkeypatch.setenv("PG_USER", "postgres")
    monkeypatch.setenv("PG_PASSWORD", "pass")
    monkeypatch.setenv("PG_HOST", "postgres")  # Test expects "postgres" not "localhost"
    monkeypatch.setenv("PG_PORT", "5432")
    monkeypatch.setenv("PG_DATABASE", "awa")

    dsn = build_dsn(sync=False)
    assert dsn.startswith("postgresql+asyncpg://")
    assert "@postgres:" in dsn
