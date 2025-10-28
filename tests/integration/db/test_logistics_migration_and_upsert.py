from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import text

from services.logistics_etl import repository

pytestmark = [pytest.mark.integration]


def test_logistics_tables_and_upsert(db_engine):
    source = "http://integration.example/rates.csv"
    rows = [
        {
            "carrier": "INT-DHL",
            "origin": "DE",
            "dest": "FR",
            "service": "express",
            "eur_per_kg": 1.1,
            "effective_from": "2024-01-01",
            "effective_to": "2024-02-01",
            "source": source,
        },
        {
            "carrier": "INT-DHL",
            "origin": "DE",
            "dest": "FR",
            "service": "express",
            "eur_per_kg": 1.2,
            "effective_from": "2024-01-01",
            "effective_to": "2024-02-15",
            "source": source,
        },
    ]

    with db_engine.begin() as conn:
        conn.execute(
            text("DELETE FROM logistics_rates WHERE source = :source"),
            {"source": source},
        )
        conn.execute(
            text("DELETE FROM logistics_loadlog WHERE source = :source"),
            {"source": source},
        )

    async def _run() -> None:
        await repository.upsert_many(
            table="logistics_rates",
            key_cols=["carrier", "origin", "dest", "service", "effective_from"],
            rows=rows,
            update_columns=["eur_per_kg", "effective_to", "updated_at"],
        )
        await repository.mark_load(source, "sha123", "seq1", len(rows))
        await repository.mark_load(source, "sha123", "seq1", len(rows))

    asyncio.run(_run())

    with db_engine.connect() as conn:
        rates_table = conn.execute(
            text("SELECT to_regclass('logistics_rates')")
        ).scalar()
        loadlog_table = conn.execute(
            text("SELECT to_regclass('logistics_loadlog')")
        ).scalar()
        assert rates_table is not None
        assert loadlog_table is not None

        rate_count = conn.execute(
            text(
                """
                SELECT COUNT(*)
                  FROM logistics_rates
                 WHERE carrier = :carrier
                   AND origin = :origin
                   AND dest = :dest
                   AND service = :service
                   AND COALESCE(effective_from, DATE '1900-01-01') = DATE '2024-01-01'
                """
            ),
            {
                "carrier": "INT-DHL",
                "origin": "DE",
                "dest": "FR",
                "service": "express",
            },
        ).scalar()
        assert rate_count == 1

        rows_logged = conn.execute(
            text("SELECT COUNT(*) FROM logistics_loadlog WHERE source = :source"),
            {"source": source},
        ).scalar()
        assert rows_logged == 1

        unique_sha = conn.execute(
            text(
                """
                SELECT COUNT(*)
                  FROM logistics_loadlog
                 WHERE source = :source
                   AND sha256 = :sha
                """
            ),
            {"source": source, "sha": "sha123"},
        ).scalar()
        assert unique_sha == 1
