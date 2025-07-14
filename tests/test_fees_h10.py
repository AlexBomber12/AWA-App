import os
import importlib
from services.common.dsn import build_dsn

import pytest
from httpx import Response
from sqlalchemy import create_engine, text

pytest.importorskip("celery")
respx = pytest.importorskip("respx")
from services.fees_h10 import client, repository, worker  # noqa: E402


@respx.mock
@pytest.mark.asyncio
async def test_fetch_fees():
    route = respx.get(client.BASE.format("A1")).mock(
        return_value=Response(200, json={"fulfillmentFee": 1, "referralFee": 2, "storageFee": 0.5})
    )
    os.environ["HELIUM10_KEY"] = "k"
    row = await client.fetch_fees("A1")
    assert route.called
    assert row["asin"] == "A1"
    assert row["fulfil_fee"] == 1
    assert row["referral_fee"] == 2
    assert row["storage_fee"] == 0.5


@pytest.mark.asyncio
async def test_repository_upsert(tmp_path, monkeypatch, pg_pool):
    importlib.reload(repository)
    engine = create_engine(build_dsn())
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS fees_raw (
                asin TEXT PRIMARY KEY,
                fulfil_fee NUMERIC(10,2) NOT NULL,
                referral_fee NUMERIC(10,2) NOT NULL,
                storage_fee NUMERIC(10,2) NOT NULL DEFAULT 0,
                currency CHAR(3) NOT NULL DEFAULT '€',
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    await repository.upsert(
        {
            "asin": "A1",
            "fulfil_fee": 1.0,
            "referral_fee": 1.0,
            "storage_fee": 1.0,
            "currency": "EUR",
        }
    )
    await repository.upsert(
        {
            "asin": "A1",
            "fulfil_fee": 2.0,
            "referral_fee": 3.0,
            "storage_fee": 4.0,
            "currency": "EUR",
        }
    )
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT fulfil_fee, referral_fee, storage_fee FROM fees_raw WHERE asin='A1'")
        ).fetchone()
    assert row == (2.0, 3.0, 4.0)


@respx.mock
def test_refresh_fees(tmp_path, monkeypatch, pg_pool):
    importlib.reload(repository)
    importlib.reload(worker)
    engine = create_engine(build_dsn())
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS fees_raw (
                asin TEXT PRIMARY KEY,
                fulfil_fee NUMERIC(10,2) NOT NULL,
                referral_fee NUMERIC(10,2) NOT NULL,
                storage_fee NUMERIC(10,2) NOT NULL DEFAULT 0,
                currency CHAR(3) NOT NULL DEFAULT '€',
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    monkeypatch.setattr(worker, "list_active_asins", lambda: ["A1", "A2", "A3"])
    for asin in ["A1", "A2", "A3"]:
        respx.get(client.BASE.format(asin)).mock(
            return_value=Response(
                200, json={"fulfillmentFee": 1, "referralFee": 1, "storageFee": 1}
            )
        )
    worker.refresh_fees()
    with engine.connect() as conn:
        cnt = conn.execute(text("SELECT count(*) FROM fees_raw"))
        assert cnt.scalar() == 3
