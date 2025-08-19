import os

import pytest
from sqlalchemy import text

TEST_TABLE = os.getenv("FEES_RAW_TABLE", "test_fees_raw")


@pytest.fixture
def ensure_test_fees_raw_table(pg_engine):
    with pg_engine.begin() as c:
        c.execute(
            text(
                f"""
            CREATE TABLE IF NOT EXISTS {TEST_TABLE}(
                asin text NOT NULL,
                marketplace text NOT NULL,
                fee_type text NOT NULL,
                amount numeric,
                currency text,
                source text,
                effective_date date,
                PRIMARY KEY (asin, marketplace, fee_type)
            );
            """
            )
        )
        c.execute(text(f"TRUNCATE {TEST_TABLE};"))
    yield
    with pg_engine.begin() as c:
        c.execute(text(f"TRUNCATE {TEST_TABLE};"))
