import os

from services.common.dsn import build_dsn


def test_build_dsn_sync_suffix():
    os.environ.pop("DATABASE_URL", None)
    dsn = build_dsn(sync=True)
    assert "+psycopg" in dsn


def test_build_dsn_default_host_postgres(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("PG_HOST", raising=False)
    dsn = build_dsn(sync=False)
    assert dsn.startswith("postgresql+asyncpg://")
    assert "@postgres:" in dsn
