from __future__ import annotations

import importlib

from awa_common.dsn import build_dsn
from services.price_importer.common import db_url as common_db_url
from services.price_importer.services_common import db_url as sc_db_url


def _reset_pg_env(monkeypatch):
    for name in ("PG_SYNC_DSN", "PG_ASYNC_DSN", "DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("PG_USER", "tester")
    monkeypatch.setenv("PG_PASSWORD", "secret")
    monkeypatch.setenv("PG_DATABASE", "awa")
    monkeypatch.setenv("PG_HOST", "db.internal")
    monkeypatch.setenv("PG_PORT", "5433")


def _reload_modules():
    importlib.reload(common_db_url)
    importlib.reload(sc_db_url)


def test_price_importer_db_url_uses_shared_dsn(monkeypatch):
    _reset_pg_env(monkeypatch)
    _reload_modules()

    sync_expected = build_dsn(sync=True)
    async_expected = build_dsn(sync=False)

    assert common_db_url.make_dsn(async_=False) == sync_expected
    assert common_db_url.make_dsn(async_=True) == async_expected
    assert sc_db_url.build_url(async_=False) == sync_expected
    assert sc_db_url.build_url(async_=True) == async_expected
