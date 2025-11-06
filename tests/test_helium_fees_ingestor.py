import os

from awa_common.dsn import build_dsn

from services.etl import fba_fee_ingestor


def test_offline(monkeypatch, patch_etl_session):
    os.environ["ENABLE_LIVE"] = "0"
    os.environ["HELIUM_API_KEY"] = "k"
    os.environ["DATABASE_URL"] = build_dsn(sync=True)
    patch_etl_session("services.etl.fba_fee_ingestor")
    res = fba_fee_ingestor.main()
    assert res == 0


def test_run_twice(monkeypatch, patch_etl_session):
    os.environ["ENABLE_LIVE"] = "0"
    os.environ["HELIUM_API_KEY"] = "k"
    os.environ["DATABASE_URL"] = build_dsn(sync=True)
    patch_etl_session("services.etl.fba_fee_ingestor")

    fba_fee_ingestor.main()
    fba_fee_ingestor.main()
