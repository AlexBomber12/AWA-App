import os

import pytest
from sqlalchemy import create_engine, text

from awa_common.dsn import build_dsn

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not set"),
]


def test_indexes_exist():
    engine = create_engine(build_dsn(sync=True))
    try:
        with engine.connect() as conn:
            pk = conn.execute(text("SELECT 1 FROM pg_constraint WHERE conname='reimbursements_raw_pkey'")).scalar()
            idx = conn.execute(text("SELECT 1 FROM pg_indexes WHERE indexname='idx_returns_raw_asin'")).scalar()
            brin = conn.execute(
                text(
                    "SELECT 1 FROM pg_indexes WHERE indexname IN "
                    "('brin_returns_raw_return_date','brin_returns_raw_processed_at')"
                )
            ).scalar()
        assert pk == 1
        assert idx == 1
        assert brin == 1
    finally:
        engine.dispose()
