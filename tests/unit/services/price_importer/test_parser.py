from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, select

from services.price_importer import reader
from services.price_importer.common.models_vendor import VendorPrice
from services.price_importer.normaliser import guess_columns, normalise
from services.price_importer.repository import Repository


def test_normalise_handles_missing_headers() -> None:
    df = pd.DataFrame(
        [
            {"SKU": "SKU-1", "Unit Cost": 10.0, "Currency": "EUR"},
            {"SKU": "SKU-2", "Unit Cost": 12.5, "Currency": "USD"},
        ]
    )
    cols = guess_columns(df)
    assert cols["sku"] == "SKU"
    assert cols["cost"] == "Unit Cost"

    normalised = normalise(df)
    assert list(normalised.columns) == ["sku", "cost", "currency"]
    assert normalised.iloc[0]["sku"] == "SKU-1"


def test_reader_loads_fixture_and_filters_invalid_rows() -> None:
    fixture = Path("tests/fixtures/price_importer/sample.csv")
    assert reader.detect_format(fixture) == "csv"
    df = reader.load_file(fixture)
    assert "BROKEN_ROW" in df["sku"].astype(str).tolist()

    cleaned = normalise(df).dropna(subset=["sku", "cost"])
    rows = [row for row in cleaned.to_dict(orient="records") if isinstance(row["sku"], str)]

    assert len(rows) == 3
    assert rows[0]["currency"] == "USD"


def test_repository_upsert_prices_deduplicates_and_updates() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    repo = Repository(engine)
    vendor_id = repo.ensure_vendor("ACME")

    rows = [
        {"sku": "SKU-1", "cost": 10.0, "currency": "EUR"},
        {"sku": "SKU-1", "cost": 11.5, "currency": "EUR", "lead_time_days": 5},
        {"sku": "SKU-2", "cost": 9.0, "currency": "USD"},
    ]

    inserted, updated = repo.upsert_prices(vendor_id, rows)
    assert inserted == 2
    assert updated == 1

    with engine.connect() as conn:
        data = list(conn.execute(select(VendorPrice)).mappings())

    assert {row["sku"] for row in data} == {"SKU-1", "SKU-2"}
    sku1 = next(row for row in data if row["sku"] == "SKU-1")
    assert float(sku1["cost"]) == 11.5
    assert sku1["lead_time_days"] == 5

    inserted2, updated2 = repo.upsert_prices(vendor_id, rows)
    assert inserted2 == 0
    assert updated2 == 3


def test_repository_upsert_prices_empty_and_dry_run() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    repo = Repository(engine)
    vendor_id = repo.ensure_vendor("DryRunVendor")

    assert repo.upsert_prices(vendor_id, []) == (0, 0)
    inserted, updated = repo.upsert_prices(
        vendor_id, [{"sku": "SKU-EMPTY", "cost": 1.0, "currency": "EUR"}], dry_run=True
    )
    assert inserted == 1 and updated == 0

    with engine.connect() as conn:
        rows = list(conn.execute(select(VendorPrice)).mappings())
    assert rows == []
