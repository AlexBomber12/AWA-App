import os

import pytest
from sqlalchemy import text

LOG_TABLE = os.getenv("LOGISTICS_TEST_TABLE", "test_logistics_routes")


@pytest.fixture
def ensure_test_logistics_table(pg_engine):
    with pg_engine.begin() as c:
        c.execute(
            text(f"""
            CREATE TABLE IF NOT EXISTS {LOG_TABLE}(
                lane_id text PRIMARY KEY,
                carrier text,
                eur_per_kg numeric,
                updated_at timestamp with time zone DEFAULT now()
            );
        """)
        )
        c.execute(text(f"TRUNCATE {LOG_TABLE};"))
    yield
    with pg_engine.begin() as c:
        c.execute(text(f"TRUNCATE {LOG_TABLE};"))
