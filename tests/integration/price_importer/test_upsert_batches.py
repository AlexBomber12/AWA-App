from __future__ import annotations

import pytest
from sqlalchemy import text

from services.price_importer.repository import Repository


@pytest.mark.integration
def test_price_importer_upsert_batches(pg_engine) -> None:
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM vendor_prices"))
        conn.execute(text("DELETE FROM vendors WHERE name = 'BatchVendor'"))

    repo = Repository(pg_engine)
    vendor_id = repo.ensure_vendor("BatchVendor")

    initial_rows = [
        {"sku": "SKU-1", "unit_price": 10.0, "currency": "EUR", "moq": 1, "lead_time_d": 5},
        {"sku": "SKU-2", "unit_price": 12.5, "currency": "USD", "moq": 2, "lead_time_d": 7},
    ]
    inserted, updated = repo.upsert_prices(vendor_id, initial_rows)
    assert inserted == 2 and updated == 0

    batch_rows = [
        {"sku": "SKU-1", "unit_price": 11.0, "currency": "eur", "moq": 3, "lead_time_d": 6},
        {"sku": "SKU-3", "unit_price": 9.99, "currency": "GBP", "moq": 1, "lead_time_d": 4},
    ]
    inserted2, updated2 = repo.upsert_prices(vendor_id, batch_rows)
    assert inserted2 == 1 and updated2 == 1

    with pg_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT sku, cost, currency, moq, lead_time_days FROM vendor_prices WHERE vendor_id = :vid"),
            {"vid": vendor_id},
        ).fetchall()

    assert {row[0] for row in rows} == {"SKU-1", "SKU-2", "SKU-3"}
    sku1 = next(row for row in rows if row[0] == "SKU-1")
    assert float(sku1[1]) == pytest.approx(11.0)
    assert sku1[2] == "EUR"
    assert sku1[3] == 3
