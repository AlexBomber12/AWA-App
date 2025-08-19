import os

import pytest
from sqlalchemy import create_engine, text


def _db_url() -> str:
    return (
        os.getenv("DATABASE_URL")
        or os.getenv("ASYNC_DATABASE_URL")
        or "postgresql://postgres:postgres@localhost:5432/postgres"
    )


@pytest.fixture(scope="session")
def pg_engine():
    engine = create_engine(_db_url())
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def ensure_test_generic_table(pg_engine):
    with pg_engine.begin() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS test_generic_raw(
                \"ASIN\" text PRIMARY KEY,
                qty integer,
                price numeric
            );
            """
            )
        )
        conn.execute(text('TRUNCATE TABLE test_generic_raw;'))
    yield
    with pg_engine.begin() as conn:
        conn.execute(text('TRUNCATE TABLE test_generic_raw;'))
