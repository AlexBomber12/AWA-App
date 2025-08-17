from __future__ import annotations

from pathlib import Path

import pandas as pd

from services.etl.dialects import amazon_returns, schemas


def test_returns_schema_validation():
    df = pd.read_csv(Path('tests/fixtures/sample_returns.csv'))
    df = amazon_returns.normalise(df)
    schemas.validate(df, 'returns_report')


def test_reimbursements_schema_validation():
    df = pd.DataFrame(
        {
            'reimb_id': ['r1'],
            'reimb_date': ['2024-07-01'],
            'qty': [1],
            'amount': [10.5],
            'currency': ['USD'],
        }
    )
    schemas.validate(df, 'reimbursements_report')
