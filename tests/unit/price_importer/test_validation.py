from __future__ import annotations

from decimal import Decimal

import pytest

from services.price_importer.io import validate_price_rows


def test_validate_price_rows_normalises_fields() -> None:
    rows = [
        {"sku": " sku-1 ", "cost": "1,25", "currency": "usd", "moq": "2", "lead_time_days": "5.0"},
    ]
    result = validate_price_rows(rows)
    assert result[0]["sku"] == "sku-1"
    assert result[0]["currency"] == "USD"
    assert result[0]["moq"] == 2
    assert result[0]["lead_time_d"] == 5
    assert isinstance(result[0]["unit_price"], Decimal)
    assert float(result[0]["unit_price"]) == pytest.approx(1.25)


def test_validate_price_rows_raises_for_missing_fields() -> None:
    rows = [
        {"cost": 1, "currency": "EUR"},
        {"sku": "A1", "currency": "eur"},
    ]
    with pytest.raises(ValueError) as exc:
        validate_price_rows(rows)
    message = str(exc.value)
    assert "invalid price rows" in message.lower()
    assert "index" in message


def test_validate_price_rows_rejects_currency_length() -> None:
    with pytest.raises(ValueError):
        validate_price_rows([{"sku": "A1", "cost": 1, "currency": "EU"}])


def test_validate_price_rows_disallows_negative_cost() -> None:
    with pytest.raises(ValueError):
        validate_price_rows([{"sku": "A1", "cost": -1, "currency": "EUR"}])
