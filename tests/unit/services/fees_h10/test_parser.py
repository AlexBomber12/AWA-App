from __future__ import annotations

import csv
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.asyncio
async def test_fetch_fees_normalises_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.fees_h10 import client

    calls: dict[str, object] = {}

    class DummyClient:
        async def get_json(self, url: str, **kwargs):
            calls["method"] = "GET"
            calls["url"] = url
            calls["headers"] = kwargs.get("headers")
            return {
                "fulfillmentFee": "1.50",
                "referralFee": 0,
                "storageFee": "-0.25",
                "currency": "GBP",
            }

    monkeypatch.setattr(client, "_HTTP_CLIENT", DummyClient(), raising=False)
    monkeypatch.setattr(client, "H10_KEY", "secret", raising=False)

    row = await client.fetch_fees("ASIN123")

    assert calls["url"].endswith("ASIN123")
    assert calls["headers"]["Authorization"].startswith("Bearer ")
    assert pytest.approx(row["fulfil_fee"]) == 1.5
    assert pytest.approx(row["referral_fee"]) == 0.0
    assert pytest.approx(row["storage_fee"]) == -0.25
    assert row["currency"] == "GBP"


@pytest.mark.asyncio
async def test_fetch_fees_handles_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.fees_h10 import client

    class DummyClient:
        async def get_json(self, url: str, **kwargs):
            assert kwargs.get("headers") == {}
            return {"fulfillmentFee": 2}

    monkeypatch.setattr(client, "_HTTP_CLIENT", DummyClient(), raising=False)
    monkeypatch.setattr(client, "H10_KEY", "", raising=False)

    row = await client.fetch_fees("B00TEST")

    assert pytest.approx(row["fulfil_fee"]) == 2.0
    assert row["referral_fee"] == 0.0
    assert row["storage_fee"] == 0.0


def test_upsert_fees_raw_processes_fixture() -> None:
    from services.fees_h10 import repository as repo

    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE fees_raw (
                asin TEXT NOT NULL,
                marketplace TEXT NOT NULL,
                fee_type TEXT NOT NULL,
                amount REAL,
                currency TEXT,
                source TEXT,
                effective_date DATE,
                PRIMARY KEY (asin, marketplace, fee_type)
            )
            """
        )

    fixture_path = Path("tests/fixtures/fees_h10/sample.csv")
    rows = []
    with fixture_path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            amount = row.get("amount")
            if not amount:
                continue  # skip malformed line
            rows.append(
                {
                    "asin": row["sku"],
                    "marketplace": "US",
                    "fee_type": row["fee_type"],
                    "amount": float(amount),
                    "currency": row.get("currency") or "USD",
                    "source": "fixture",
                    "effective_date": (row.get("reported_at") or "")[:10] or None,
                }
            )

    summary = repo.upsert_fees_raw(engine, rows, testing=True)
    assert summary["inserted"] == 3
    assert summary["updated"] in (-1, 0)

    rows_update = [
        {**rows[0], "amount": rows[0]["amount"] + 0.5},
        rows[1],
        rows[2],
    ]

    summary2 = repo.upsert_fees_raw(engine, rows_update, testing=True)
    assert summary2["inserted"] == 0
    assert summary2["updated"] in (-1, 1)

    with engine.connect() as conn:
        total_rows = conn.execute(text("SELECT COUNT(*) FROM fees_raw")).scalar_one()
        updated_amount = conn.execute(
            text("SELECT amount FROM fees_raw WHERE asin = :asin AND marketplace = 'US' AND fee_type = :fee_type"),
            {"asin": rows[0]["asin"], "fee_type": rows[0]["fee_type"]},
        ).scalar_one()

    assert total_rows == 3
    assert pytest.approx(updated_amount) == rows[0]["amount"] + 0.5


def test_upsert_fees_raw_empty_input_returns_zero_counts() -> None:
    from services.fees_h10 import repository as repo

    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE fees_raw (
                asin TEXT NOT NULL,
                marketplace TEXT NOT NULL,
                fee_type TEXT NOT NULL,
                amount REAL,
                currency TEXT,
                source TEXT,
                effective_date DATE,
                PRIMARY KEY (asin, marketplace, fee_type)
            )
            """
        )

    assert repo.upsert_fees_raw(engine, [], testing=True) == {
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
    }
