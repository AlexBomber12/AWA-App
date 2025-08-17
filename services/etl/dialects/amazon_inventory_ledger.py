from __future__ import annotations

import pandas as pd
from pandas import DataFrame

from . import normalise_headers

SYNONYMS = {
    "event_date": ["event-date", "date"],
    "asin": ["asin"],
    "sku": ["sku"],
    "fnsku": ["fnsku"],
    "warehouse": ["warehouse", "warehouse-id"],
    "event_type": ["event-type", "transaction-type"],
    "reference_id": ["reference-id"],
    "quantity": ["quantity", "qty"],
}

TARGET_TABLE = "inventory_ledger_raw"
TARGET_SCHEMA = None
TARGET_COLUMNS = [
    "event_date",
    "asin",
    "sku",
    "fnsku",
    "warehouse",
    "event_type",
    "reference_id",
    "quantity",
]
CONFLICT_COLS = None


def normalise(df: DataFrame) -> DataFrame:
    lower = {c.lower(): c for c in df.columns}
    for key, options in SYNONYMS.items():
        for opt in options:
            if opt in lower:
                df = df.rename(columns={lower[opt]: key})
                break
    for col in TARGET_COLUMNS:
        if col not in df.columns:
            if col == "quantity":
                df[col] = pd.Series([0] * len(df), dtype="Int64")
            else:
                df[col] = pd.NA
    return df[TARGET_COLUMNS]


def detect(columns: list[str]) -> bool:
    cols = set(normalise_headers(columns))
    has_date = any(opt in cols for opt in SYNONYMS["event_date"])
    has_type = any(opt in cols for opt in SYNONYMS["event_type"])
    has_id = any(
        opt in cols for opt in SYNONYMS["fnsku"] + SYNONYMS["sku"] + SYNONYMS["asin"]
    )
    return has_date and has_type and has_id
