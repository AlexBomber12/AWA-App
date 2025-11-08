from __future__ import annotations

from collections.abc import Generator, Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd
import structlog

from .normaliser import normalise
from .reader import detect_format, load_file

logger = structlog.get_logger(__name__)

DEFAULT_BATCH_SIZE = 1000


@dataclass(frozen=True)
class PriceRow:
    sku: str
    cost: Decimal
    currency: str
    moq: int
    lead_time_days: int


def _parse_sku(value: Any) -> str:
    sku = str(value or "").strip()
    if not sku:
        raise ValueError("sku missing")
    return sku


def _parse_currency(value: Any) -> str:
    currency = str(value or "").strip().upper()
    if not currency:
        raise ValueError("currency missing")
    if len(currency) != 3:
        raise ValueError("currency must be a 3-letter ISO code")
    return currency


def _parse_cost(value: Any) -> Decimal:
    if value is None:
        raise ValueError("cost missing")
    if isinstance(value, (int, float, Decimal)):
        candidate = Decimal(str(value))
    else:
        text = str(value).strip()
        if not text:
            raise ValueError("cost missing")
        if "," in text and "." not in text:
            text = text.replace(",", ".")
        try:
            candidate = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError("cost not numeric") from exc
    if candidate.is_nan():
        raise ValueError("cost NaN")
    if candidate < 0:
        raise ValueError("cost negative")
    return candidate


def _parse_int(value: Any, *, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        # Handle pandas NA / floats by casting to float first.
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return default
            return int(float(text))
        return int(float(value))
    except (TypeError, ValueError):
        return default


def validate_price_rows(rows: Sequence[dict[str, Any]]) -> list[PriceRow]:
    """Validate and normalise a batch of price rows."""
    valid: list[PriceRow] = []
    errors: list[dict[str, Any]] = []

    for idx, raw in enumerate(rows):
        try:
            sku = _parse_sku(raw.get("sku"))
            cost = _parse_cost(raw.get("cost"))
            currency = _parse_currency(raw.get("currency"))
            moq = _parse_int(raw.get("moq"), default=0)
            lead_time = _parse_int(raw.get("lead_time_days"), default=0)
            valid.append(PriceRow(sku=sku, cost=cost, currency=currency, moq=moq, lead_time_days=lead_time))
        except ValueError as exc:
            errors.append({"index": idx, "error": str(exc), "row": dict(raw)})

    if errors:
        sample = errors[:3]
        raise ValueError(
            f"{len(errors)} invalid price rows; sample={sample}",
        )
    return valid


def _iter_csv_chunks(path: str | Path, batch_size: int) -> Generator[pd.DataFrame]:
    """Yield CSV chunks while retrying encodings and delimiters like the legacy reader."""
    encodings = ("utf-8", "utf-8-sig", "cp1252")
    for enc in encodings:
        try:
            reader = pd.read_csv(
                path,
                sep=None,
                engine="python",
                encoding=enc,
                chunksize=batch_size,
            )
            yield from reader
            return
        except UnicodeDecodeError:
            continue
        except Exception:
            continue

    for sep in (",", ";", "\t", "|"):
        try:
            reader = pd.read_csv(path, sep=sep, chunksize=batch_size)
            yield from reader
            return
        except Exception:
            continue
    raise RuntimeError(f"Failed to stream CSV file: {path}")


def _iter_dataframe_batches(df: pd.DataFrame, batch_size: int) -> Generator[pd.DataFrame]:
    total = len(df.index)
    if total == 0:
        return
    for start in range(0, total, batch_size):
        yield df.iloc[start : start + batch_size]


def iter_price_batches(path: str | Path, batch_size: int = DEFAULT_BATCH_SIZE) -> Iterable[list[PriceRow]]:
    """Yield validated, normalised price rows in bounded-size batches."""
    fmt = detect_format(path)
    if fmt == "csv":
        frames = _iter_csv_chunks(path, batch_size)
    else:
        frames = _iter_dataframe_batches(load_file(path), batch_size)

    for frame in frames:
        if frame is None or frame.empty:
            continue
        cleaned = normalise(frame)
        records = cleaned.to_dict(orient="records")
        if not records:
            continue
        yield validate_price_rows(records)
