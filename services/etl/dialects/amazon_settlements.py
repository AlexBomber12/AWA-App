from __future__ import annotations

import numpy as np
import pandas as pd
from pandas import DataFrame

from . import normalise_headers

SYNONYMS = {
    "settlement_id": ["settlement-id"],
    "posted_date": ["posted-date"],
    "transaction_type": ["transaction-type"],
    "order_id": ["order-id"],
    "sku": ["sku"],
    "asin": ["asin"],
    "marketplace": ["marketplace-name", "marketplace"],
    "amount_type": ["amount-type"],
    "amount": ["amount"],
    "currency": ["currency", "currency-code"],
    "transaction_id": ["transaction-id"],
}

TARGET_TABLE = "settlements_txn_raw"
TARGET_SCHEMA = None
TARGET_COLUMNS = [
    "settlement_id",
    "posted_date",
    "transaction_type",
    "order_id",
    "sku",
    "asin",
    "marketplace",
    "amount_type",
    "amount",
    "currency",
    "transaction_id",
]
CONFLICT_COLS = ("transaction_id",)


def normalise(df: DataFrame) -> DataFrame:
    lower = {c.lower(): c for c in df.columns}
    for key, options in SYNONYMS.items():
        for opt in options:
            if opt in lower:
                df = df.rename(columns={lower[opt]: key})
                break
    for col in TARGET_COLUMNS:
        if col not in df.columns:
            if col == "amount":
                df[col] = pd.Series([np.nan] * len(df), dtype="float64")
            else:
                df[col] = pd.NA
    return df[TARGET_COLUMNS]


def detect(columns: list[str]) -> bool:
    cols = set(normalise_headers(columns))
    required = ["settlement-id", "posted-date", "amount-type", "amount"]
    return all(c in cols for c in required)
