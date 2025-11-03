from __future__ import annotations

import os
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from services.etl.dialects import (
    amazon_ads_sp_cost,
    amazon_fee_preview,
    amazon_inventory_ledger,
    amazon_settlements,
)
from services.worker.copy_loader import copy_df_via_temp

TEST_DSN = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(TEST_DSN is None, reason="TEST_DATABASE_URL not set")


@pytest.fixture(scope="module")
def engine():
    engine = create_engine(TEST_DSN)
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS test_ingest"))
        conn.execute(text("DROP TABLE IF EXISTS test_ingest.reimbursements_raw CASCADE"))
        conn.execute(
            text(
                """
                CREATE TABLE test_ingest.reimbursements_raw(
                    reimb_id text PRIMARY KEY,
                    reimb_date timestamp,
                    qty int,
                    amount double precision,
                    currency text,
                    asin text
                )
                """
            )
        )
        conn.execute(text("DROP TABLE IF EXISTS test_ingest.returns_raw CASCADE"))
        conn.execute(
            text(
                """
                CREATE TABLE test_ingest.returns_raw(
                    asin text,
                    return_date timestamp,
                    qty int,
                    refund_amount double precision,
                    currency text
                )
                """
            )
        )
        conn.execute(text("DROP TABLE IF EXISTS test_ingest.fee_preview_raw CASCADE"))
        conn.execute(
            text(
                """
                CREATE TABLE test_ingest.fee_preview_raw(
                    asin text,
                    sku text,
                    fnsku text,
                    referral_fee double precision,
                    fulfillment_fee double precision,
                    storage_fee double precision,
                    estimated_fee_total double precision NOT NULL,
                    currency text NOT NULL,
                    captured_at timestamp
                )
                """
            )
        )
        conn.execute(text("DROP TABLE IF EXISTS test_ingest.inventory_ledger_raw CASCADE"))
        conn.execute(
            text(
                """
                CREATE TABLE test_ingest.inventory_ledger_raw(
                    event_date timestamp,
                    asin text,
                    sku text,
                    fnsku text,
                    warehouse text,
                    event_type text,
                    reference_id text,
                    quantity int
                )
                """
            )
        )
        conn.execute(text("DROP TABLE IF EXISTS test_ingest.ads_sp_cost_daily_raw CASCADE"))
        conn.execute(
            text(
                """
                CREATE TABLE test_ingest.ads_sp_cost_daily_raw(
                    date date,
                    campaign_id text,
                    ad_group_id text,
                    keyword_id text,
                    targeting text,
                    impressions int,
                    clicks int,
                    spend double precision,
                    orders int,
                    sales double precision,
                    currency text,
                    UNIQUE(date, campaign_id, ad_group_id, keyword_id)
                )
                """
            )
        )
        conn.execute(text("DROP TABLE IF EXISTS test_ingest.settlements_txn_raw CASCADE"))
        conn.execute(
            text(
                """
                CREATE TABLE test_ingest.settlements_txn_raw(
                    settlement_id text,
                    posted_date timestamp,
                    transaction_type text,
                    order_id text,
                    sku text,
                    asin text,
                    marketplace text,
                    amount_type text,
                    amount double precision,
                    currency text,
                    transaction_id text,
                    UNIQUE(transaction_id)
                )
                """
            )
        )
    yield engine
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS test_ingest CASCADE"))
    engine.dispose()


def test_upsert(engine):
    cols = ["reimb_id", "reimb_date", "qty", "amount", "currency", "asin"]
    df1 = pd.DataFrame(
        [
            {
                "reimb_id": "r1",
                "reimb_date": datetime(2024, 1, 1),
                "qty": 1,
                "amount": 10.0,
                "currency": "USD",
                "asin": "A",
            },
            {
                "reimb_id": "r2",
                "reimb_date": datetime(2024, 1, 2),
                "qty": 2,
                "amount": 20.0,
                "currency": "USD",
                "asin": "B",
            },
        ]
    )
    copy_df_via_temp(
        engine,
        df1,
        target_table="reimbursements_raw",
        target_schema="test_ingest",
        columns=cols,
        conflict_cols=("reimb_id",),
    )

    df2 = pd.DataFrame(
        [
            {
                "reimb_id": "r1",
                "reimb_date": datetime(2024, 1, 1),
                "qty": 1,
                "amount": 30.0,
                "currency": "USD",
                "asin": "A",
            },
            {
                "reimb_id": "r2",
                "reimb_date": datetime(2024, 1, 2),
                "qty": 2,
                "amount": 20.0,
                "currency": "USD",
                "asin": "B",
            },
        ]
    )
    copy_df_via_temp(
        engine,
        df2,
        target_table="reimbursements_raw",
        target_schema="test_ingest",
        columns=cols,
        conflict_cols=("reimb_id",),
    )

    with engine.connect() as conn:
        cnt = conn.execute(text("SELECT count(*) FROM test_ingest.reimbursements_raw")).scalar()
        amt = conn.execute(
            text("SELECT amount FROM test_ingest.reimbursements_raw WHERE reimb_id='r1'")
        ).scalar()
    assert cnt == 2
    assert amt == 30.0


def test_append_only(engine):
    cols = ["asin", "return_date", "qty", "refund_amount", "currency"]
    df = pd.DataFrame(
        [
            {
                "asin": "A1",
                "return_date": datetime(2024, 1, 1),
                "qty": 1,
                "refund_amount": 5.0,
                "currency": "USD",
            },
            {
                "asin": "A2",
                "return_date": datetime(2024, 1, 2),
                "qty": 2,
                "refund_amount": 10.0,
                "currency": "USD",
            },
        ]
    )
    copy_df_via_temp(
        engine,
        df,
        target_table="returns_raw",
        target_schema="test_ingest",
        columns=cols,
    )
    copy_df_via_temp(
        engine,
        df,
        target_table="returns_raw",
        target_schema="test_ingest",
        columns=cols,
    )
    with engine.connect() as conn:
        cnt = conn.execute(text("SELECT count(*) FROM test_ingest.returns_raw")).scalar()
    assert cnt == 4


def test_null_handling(engine):
    cols = ["reimb_id", "reimb_date", "qty", "amount", "currency", "asin"]
    df = pd.DataFrame(
        [
            {
                "reimb_id": "rnull",
                "reimb_date": datetime(2024, 1, 3),
                "qty": 1,
                "amount": np.nan,
                "currency": "",
                "asin": "A",
            }
        ]
    )
    copy_df_via_temp(
        engine,
        df,
        target_table="reimbursements_raw",
        target_schema="test_ingest",
        columns=cols,
        conflict_cols=("reimb_id",),
    )
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT amount, currency FROM test_ingest.reimbursements_raw WHERE reimb_id='rnull'"
            )
        ).one()
    assert row.amount is None
    assert row.currency is None


def test_fee_preview_append(engine):
    df = pd.DataFrame({"asin": ["A1"], "estimated_fee_total": [1.0], "currency": ["USD"]})
    copy_df_via_temp(
        engine,
        amazon_fee_preview.normalise(df),
        target_table="fee_preview_raw",
        target_schema="test_ingest",
        columns=amazon_fee_preview.TARGET_COLUMNS,
    )
    copy_df_via_temp(
        engine,
        amazon_fee_preview.normalise(df),
        target_table="fee_preview_raw",
        target_schema="test_ingest",
        columns=amazon_fee_preview.TARGET_COLUMNS,
    )
    with engine.connect() as conn:
        cnt = conn.execute(text("SELECT count(*) FROM test_ingest.fee_preview_raw")).scalar()
    assert cnt == 2


def test_inventory_ledger_append(engine):
    df = pd.DataFrame(
        {
            "event_date": [datetime(2024, 1, 1)],
            "event_type": ["Adjust"],
            "sku": ["S1"],
            "quantity": [1],
        }
    )
    copy_df_via_temp(
        engine,
        amazon_inventory_ledger.normalise(df),
        target_table="inventory_ledger_raw",
        target_schema="test_ingest",
        columns=amazon_inventory_ledger.TARGET_COLUMNS,
    )
    with engine.connect() as conn:
        cnt = conn.execute(text("SELECT count(*) FROM test_ingest.inventory_ledger_raw")).scalar()
    assert cnt == 1


def test_ads_sp_cost_upsert(engine):
    df1 = pd.DataFrame(
        {
            "date": [datetime(2024, 1, 1)],
            "campaign_id": ["c1"],
            "ad_group_id": ["g1"],
            "keyword_id": ["k1"],
            "impressions": [10],
            "clicks": [1],
            "spend": [0.5],
        }
    )
    copy_df_via_temp(
        engine,
        amazon_ads_sp_cost.normalise(df1),
        target_table="ads_sp_cost_daily_raw",
        target_schema="test_ingest",
        columns=amazon_ads_sp_cost.TARGET_COLUMNS,
        conflict_cols=amazon_ads_sp_cost.CONFLICT_COLS,
    )
    df2 = df1.copy()
    df2["spend"] = [1.0]
    copy_df_via_temp(
        engine,
        amazon_ads_sp_cost.normalise(df2),
        target_table="ads_sp_cost_daily_raw",
        target_schema="test_ingest",
        columns=amazon_ads_sp_cost.TARGET_COLUMNS,
        conflict_cols=amazon_ads_sp_cost.CONFLICT_COLS,
    )
    with engine.connect() as conn:
        row = conn.execute(text("SELECT spend FROM test_ingest.ads_sp_cost_daily_raw")).scalar()
    assert row == 1.0


def test_settlements_txn_upsert(engine):
    df1 = pd.DataFrame(
        {
            "settlement_id": ["s1"],
            "posted_date": [datetime(2024, 1, 1)],
            "transaction_type": ["Order"],
            "amount_type": ["ItemPrice"],
            "amount": [5.0],
            "currency": ["USD"],
            "transaction_id": ["t1"],
        }
    )
    copy_df_via_temp(
        engine,
        amazon_settlements.normalise(df1),
        target_table="settlements_txn_raw",
        target_schema="test_ingest",
        columns=amazon_settlements.TARGET_COLUMNS,
        conflict_cols=amazon_settlements.CONFLICT_COLS,
    )
    df2 = df1.copy()
    df2["amount"] = [10.0]
    copy_df_via_temp(
        engine,
        amazon_settlements.normalise(df2),
        target_table="settlements_txn_raw",
        target_schema="test_ingest",
        columns=amazon_settlements.TARGET_COLUMNS,
        conflict_cols=amazon_settlements.CONFLICT_COLS,
    )
    with engine.connect() as conn:
        amt = conn.execute(text("SELECT amount FROM test_ingest.settlements_txn_raw")).scalar()
    assert amt == 10.0
