from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

_SPACE_RE = re.compile(r"\s+")
_CURRENCY_ALIASES = {
    "€": "EUR",
    "EUR": "EUR",
    "EURO": "EUR",
    "EUROS": "EUR",
    "$": "USD",
    "USD": "USD",
    "US$": "USD",
    "GBP": "GBP",
    "£": "GBP",
}
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y.%m.%d")


def normalize_vendor_name(value: str | None) -> str:
    """Trim and collapse whitespace for vendor identifiers."""
    text = _require_text(value, field="vendor")
    normalized = " ".join(text.split())
    if not normalized:
        raise ValueError("vendor name missing")
    return normalized


def normalize_sku(value: Any) -> str:
    """Trim SKU identifiers."""
    text = _require_text(value, field="sku")
    return text


def normalize_currency(value: Any) -> str:
    """Map currency symbols or names to ISO-4217 codes."""
    text = _require_text(value, field="currency")
    collapsed = text.replace(" ", "").replace("_", "")
    normalized = collapsed.upper()
    resolved = _CURRENCY_ALIASES.get(normalized)
    if resolved:
        return resolved
    if len(normalized) == 3 and normalized.isalpha():
        return normalized
    raise ValueError(f"unsupported currency: {value}")


def parse_decimal(value: Any) -> Decimal:
    """Parse numbers that may use comma or dot decimals."""
    if value is None or value == "":
        raise ValueError("value missing")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).strip()
    if not text:
        raise ValueError("value missing")
    candidate = text.replace(" ", "")
    if candidate.count(",") == 1 and candidate.count(".") == 0:
        candidate = candidate.replace(",", ".")
    elif candidate.count(",") > 0 and candidate.count(".") > 0:
        candidate = candidate.replace(",", "")
    try:
        parsed = Decimal(candidate)
    except InvalidOperation as exc:
        raise ValueError(f"invalid decimal: {value}") from exc
    if parsed.is_nan():
        raise ValueError("value is NaN")
    return parsed


def parse_date(value: Any) -> date:
    """Parse dates from multiple string formats."""
    if value is None or value == "":
        raise ValueError("date missing")
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _require_text(value, field="date")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date()
    except ValueError as exc:
        raise ValueError(f"invalid date: {value}") from exc


def coalesce_str(*values: str | None) -> str | None:
    """Return the first non-empty trimmed string."""
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def strip_and_lower(value: str | None) -> str | None:
    """Trim text and convert to lowercase when present."""
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return text.lower()


def _require_text(value: Any, *, field: str) -> str:
    if value is None:
        raise ValueError(f"{field} missing")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} missing")
    return text


__all__ = [
    "coalesce_str",
    "normalize_currency",
    "normalize_sku",
    "normalize_vendor_name",
    "parse_date",
    "parse_decimal",
    "strip_and_lower",
]
