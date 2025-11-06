from __future__ import annotations

import time

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from awa_common.dsn import build_dsn

pytestmark = [pytest.mark.integration]


def test_load_log_schema_enforces_uniqueness(pg_pool) -> None:
    engine = create_engine(build_dsn(sync=True))
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text(
                    """
                    INSERT INTO load_log (source, idempotency_key, status, payload_meta)
                    VALUES (:source, :key, 'pending', '{}'::jsonb)
                    RETURNING id, created_at, updated_at
                    """
                ),
                {"source": "etl", "key": "abc123"},
            )
            row = result.first()
            assert row is not None
            load_log_id = row.id
            created_at = row.created_at
            updated_at = row.updated_at
            assert created_at == updated_at

        with engine.begin() as conn:
            with pytest.raises(IntegrityError):
                conn.execute(
                    text(
                        """
                        INSERT INTO load_log (source, idempotency_key, status, payload_meta)
                        VALUES (:source, :key, 'pending', '{}'::jsonb)
                        """
                    ),
                    {"source": "etl", "key": "abc123"},
                )

        time.sleep(0.01)
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE load_log SET status='success' WHERE id=:id"),
                {"id": load_log_id},
            )
            refreshed = conn.execute(
                text("SELECT status, updated_at FROM load_log WHERE id=:id"),
                {"id": load_log_id},
            ).first()
            assert refreshed.status == "success"
            assert refreshed.updated_at > created_at
    finally:
        engine.dispose()
