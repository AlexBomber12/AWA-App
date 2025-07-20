import os

import pytest

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


@pytest.mark.parametrize("env", [True, False])
def test_build_dsn_variants(env, monkeypatch):
    if env:
        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h/db")
    else:
        for var in [
            "DATABASE_URL",
            "PG_USER",
            "PG_PASSWORD",
            "PG_HOST",
            "PG_PORT",
            "PG_DATABASE",
        ]:
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("PG_USER", "u")
        monkeypatch.setenv("PG_PASSWORD", "p")
        monkeypatch.setenv("PG_HOST", "h")
        monkeypatch.setenv("PG_PORT", "5432")
        monkeypatch.setenv("PG_DATABASE", "db")
    dsn = build_dsn(sync=False)
    assert "asyncpg" in dsn
