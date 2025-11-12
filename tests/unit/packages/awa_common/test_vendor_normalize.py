from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from awa_common import vendor


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  Acme  Corp ", "Acme Corp"),
        ("\tFoo\tBar\n", "Foo Bar"),
    ],
)
def test_normalize_vendor_name(raw: str, expected: str) -> None:
    assert vendor.normalize_vendor_name(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        (" sku-123 ", "sku-123"),
        ("ab c d", "ab c d"),
    ],
)
def test_normalize_sku(raw: str, expected: str) -> None:
    assert vendor.normalize_sku(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        (" eur ", "EUR"),
        ("Euro", "EUR"),
        ("€", "EUR"),
        (" usd", "USD"),
    ],
)
def test_normalize_currency(raw: str, expected: str) -> None:
    assert vendor.normalize_currency(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("12.34", Decimal("12.34")),
        ("12,34", Decimal("12.34")),
        ("1 234,56", Decimal("1234.56")),
        (123, Decimal("123")),
    ],
)
def test_parse_decimal(raw: object, expected: Decimal) -> None:
    assert vendor.parse_decimal(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2024-01-15", date(2024, 1, 15)),
        ("15/01/2024", date(2024, 1, 15)),
        ("01/15/2024", date(2024, 1, 15)),
    ],
)
def test_parse_date_formats(raw: str, expected: date) -> None:
    assert vendor.parse_date(raw) == expected


def test_coalesce_str() -> None:
    assert vendor.coalesce_str(None, "  ", " foo ", "bar") == "foo"
    assert vendor.coalesce_str(None, "") is None


def test_strip_and_lower() -> None:
    assert vendor.strip_and_lower("  Hello ") == "hello"
    assert vendor.strip_and_lower("   ") is None
