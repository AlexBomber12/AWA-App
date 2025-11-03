from __future__ import annotations

import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema

RETURNS_SCHEMA = DataFrameSchema(
    {
        "asin": Column(pa.String, nullable=False),
        "order_id": Column(pa.String, nullable=True, required=False),
        "return_reason": Column(pa.String, nullable=True, required=False),
        "return_date": Column(pa.DateTime, nullable=False),
        "qty": Column(pa.Int64, Check.ge(0), nullable=False),
        "refund_amount": Column(pa.Float64, nullable=False),
        "currency": Column(pa.String, Check.str_length(3, 3), nullable=False),
    },
    coerce=True,
)

REIMBURSEMENTS_SCHEMA = DataFrameSchema(
    {
        "asin": Column(pa.String, nullable=True, required=False),
        "reimb_id": Column(pa.String, nullable=False),
        "reimb_date": Column(pa.DateTime, nullable=False),
        "qty": Column(pa.Int64, Check.ge(0), nullable=False),
        "amount": Column(pa.Float64, nullable=False),
        "currency": Column(pa.String, Check.str_length(3, 3), nullable=False),
        "reason_code": Column(pa.String, nullable=True, required=False),
    },
    coerce=True,
)

FEE_PREVIEW_SCHEMA = DataFrameSchema(
    {
        "asin": Column(pa.String, nullable=False),
        "sku": Column(pa.String, nullable=True, required=False),
        "fnsku": Column(pa.String, nullable=True, required=False),
        "referral_fee": Column(pa.Float64, nullable=True, required=False),
        "fulfillment_fee": Column(pa.Float64, nullable=True, required=False),
        "storage_fee": Column(pa.Float64, nullable=True, required=False),
        "estimated_fee_total": Column(pa.Float64, nullable=False),
        "currency": Column(pa.String, Check.str_length(3, 3), nullable=False),
        "captured_at": Column(pa.DateTime, nullable=False),
    },
    coerce=True,
)

INVENTORY_LEDGER_SCHEMA = DataFrameSchema(
    {
        "event_date": Column(pa.DateTime, nullable=False),
        "asin": Column(pa.String, nullable=True, required=False),
        "sku": Column(pa.String, nullable=True, required=False),
        "fnsku": Column(pa.String, nullable=True, required=False),
        "warehouse": Column(pa.String, nullable=True, required=False),
        "event_type": Column(pa.String, nullable=False),
        "reference_id": Column(pa.String, nullable=True, required=False),
        "quantity": Column(pa.Int64, nullable=True, required=False, coerce=False),
    },
    coerce=True,
)

ADS_SP_COST_DAILY_SCHEMA = DataFrameSchema(
    {
        "date": Column(pa.DateTime, nullable=False),
        "campaign_id": Column(pa.String, nullable=False),
        "ad_group_id": Column(pa.String, nullable=False),
        "keyword_id": Column(pa.String, nullable=True, required=False),
        "targeting": Column(pa.String, nullable=True, required=False),
        "impressions": Column(pa.Int64, Check.ge(0), nullable=False),
        "clicks": Column(pa.Int64, Check.ge(0), nullable=False),
        "spend": Column(pa.Float64, Check.ge(0), nullable=False),
        "orders": Column(pa.Int64, Check.ge(0), nullable=True, required=False, coerce=False),
        "sales": Column(pa.Float64, Check.ge(0), nullable=True, required=False),
        "currency": Column(pa.String, Check.str_length(3, 3), nullable=True, required=False),
    },
    coerce=True,
)

SETTLEMENTS_TXN_SCHEMA = DataFrameSchema(
    {
        "settlement_id": Column(pa.String, nullable=False),
        "posted_date": Column(pa.DateTime, nullable=False),
        "transaction_type": Column(pa.String, nullable=False),
        "order_id": Column(pa.String, nullable=True, required=False),
        "sku": Column(pa.String, nullable=True, required=False),
        "asin": Column(pa.String, nullable=True, required=False),
        "marketplace": Column(pa.String, nullable=True, required=False),
        "amount_type": Column(pa.String, nullable=False),
        "amount": Column(pa.Float64, nullable=False),
        "currency": Column(pa.String, Check.str_length(3, 3), nullable=False),
        "transaction_id": Column(pa.String, nullable=True, required=False),
    },
    coerce=True,
)


def validate(df: pd.DataFrame, dialect: str) -> pd.DataFrame:
    if dialect == "returns_report":
        schema = RETURNS_SCHEMA
    elif dialect == "reimbursements_report":
        schema = REIMBURSEMENTS_SCHEMA
    elif dialect == "fee_preview_report":
        schema = FEE_PREVIEW_SCHEMA
    elif dialect == "inventory_ledger_report":
        schema = INVENTORY_LEDGER_SCHEMA
    elif dialect == "ads_sp_cost_daily_report":
        schema = ADS_SP_COST_DAILY_SCHEMA
    elif dialect == "settlements_txn_report":
        schema = SETTLEMENTS_TXN_SCHEMA
    else:
        raise ValueError(f"Unknown dialect: {dialect}")
    return schema.validate(df, lazy=True)
