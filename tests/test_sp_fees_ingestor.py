import os

import pytest

from awa_common.dsn import build_dsn
from services.etl import sp_fees

pytestmark = pytest.mark.integration


class EngineProxy:
    def __init__(self, engine):
        self._engine = engine
        self.disposed = False

    def __getattr__(self, name):
        return getattr(self._engine, name)

    def dispose(self):
        self.disposed = True


def test_offline(monkeypatch, pg_engine, ensure_test_fees_raw_table) -> None:
    os.environ["FEES_RAW_TABLE"] = "test_fees_raw"
    os.environ["ENABLE_LIVE"] = "0"
    os.environ["SP_REFRESH_TOKEN"] = "t"
    os.environ["SP_CLIENT_ID"] = "i"
    os.environ["SP_CLIENT_SECRET"] = "s"
    os.environ["REGION"] = "EU"
    os.environ["DATABASE_URL"] = build_dsn(sync=True)
    proxy = EngineProxy(pg_engine)
    monkeypatch.setattr("services.etl.sp_fees.create_engine", lambda dsn: proxy)
    result = sp_fees.main([])
    assert result == 0
    assert proxy.disposed
