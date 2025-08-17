from __future__ import annotations

import pandas as pd

from services.etl.dialects import (
    amazon_ads_sp_cost,
    amazon_fee_preview,
    amazon_inventory_ledger,
    amazon_settlements,
    schemas,
)


def test_fee_preview_detect_normalise_schema():
    df = pd.DataFrame(
        {"asin": ["A1"], "estimated-fee-total": [1.23], "currency": ["USD"]}
    )
    assert amazon_fee_preview.detect(list(df.columns))
    df = amazon_fee_preview.normalise(df)
    schemas.validate(df, "fee_preview_report")


def test_inventory_ledger_detect_normalise_schema():
    df = pd.DataFrame(
        {
            "event-date": ["2024-01-01"],
            "event-type": ["Adjustment"],
            "sku": ["S1"],
            "quantity": [5],
        }
    )
    assert amazon_inventory_ledger.detect(list(df.columns))
    df = amazon_inventory_ledger.normalise(df)
    schemas.validate(df, "inventory_ledger_report")


def test_ads_sp_cost_detect_normalise_schema():
    df = pd.DataFrame(
        {
            "date": ["2024-01-01"],
            "campaign-id": ["c1"],
            "ad-group-id": ["g1"],
            "impressions": [10],
            "clicks": [1],
            "spend": [0.5],
        }
    )
    assert amazon_ads_sp_cost.detect(list(df.columns))
    df = amazon_ads_sp_cost.normalise(df)
    schemas.validate(df, "ads_sp_cost_daily_report")


def test_settlements_txn_detect_normalise_schema():
    df = pd.DataFrame(
        {
            "settlement-id": ["s1"],
            "posted-date": ["2024-01-01"],
            "transaction-type": ["Order"],
            "amount-type": ["ItemPrice"],
            "amount": [5.0],
            "currency": ["USD"],
        }
    )
    assert amazon_settlements.detect(list(df.columns))
    df = amazon_settlements.normalise(df)
    schemas.validate(df, "settlements_txn_report")
