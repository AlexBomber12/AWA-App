import importlib

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from services.logistics_etl import repository

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_upsert_many(pg_engine):
    importlib.reload(repository)
    dsn = pg_engine.url.render_as_string(hide_password=False)
    dsn = dsn.replace("postgresql://", "postgresql+asyncpg://")
    async_engine = create_async_engine(dsn, future=True)
    repository._engine = async_engine

    with pg_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            DROP TABLE IF EXISTS freight_rates CASCADE;
            CREATE TABLE IF NOT EXISTS freight_rates (
                lane TEXT,
                mode TEXT,
                eur_per_kg NUMERIC(10,2),
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (lane, mode)
            );
            """
        )

    data = [
        {"lane": "EU-IT\u2192US", "mode": "air", "eur_per_kg": 7.55},
        {"lane": "EU-IT\u2192US", "mode": "sea", "eur_per_kg": 2.10},
    ]
    await repository.upsert_many(data)

    with pg_engine.connect() as conn:
        rows = conn.execute(sa.text("SELECT COUNT(*) FROM freight_rates")).scalar()
    assert rows == 2
