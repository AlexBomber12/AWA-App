import os

from services.common.dsn import build_dsn


def test_build_dsn_sync_suffix():
    os.environ.pop("DATABASE_URL", None)
    dsn = build_dsn(sync=True)
    assert "+psycopg" in dsn


def test_build_dsn_default_host_postgres(monkeypatch):
    for key in [
        "DATABASE_URL",
        "PG_HOST",
        "PG_PORT",
        "PG_USER",
        "PG_PASSWORD",
        "PG_DATABASE",
    ]:
        monkeypatch.delenv(key, raising=False)
    dsn = build_dsn(sync=False)
    assert dsn.startswith("postgresql+asyncpg://")
    assert "@postgres:" in dsn
