from __future__ import annotations

from pathlib import Path

import pytest
from awa_common.dsn import build_dsn
from sqlalchemy import create_engine, text

from services.etl import fba_fee_ingestor

pytestmark = [pytest.mark.integration]


def test_fba_ingestor_skips_duplicates(monkeypatch: pytest.MonkeyPatch, pg_pool) -> None:
    monkeypatch.setenv("ENABLE_LIVE", "0")
    monkeypatch.setenv("DATABASE_URL", build_dsn(sync=True))
    fixture = Path("tests/fixtures/helium_fees_sample.json")

    engine = create_engine(build_dsn(sync=True))
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM load_log WHERE source = 'fba_fee_ingestor'"))
            conn.execute(text("DROP TABLE IF EXISTS fees_raw"))

        args = ["--offline", "--fixture-path", str(fixture)]
        assert fba_fee_ingestor.main(args) == 0
        assert fba_fee_ingestor.main(args) == 0

        with engine.begin() as conn:
            row_count = conn.execute(text("SELECT COUNT(*) FROM fees_raw")).scalar()
            assert row_count is not None and row_count > 0

            statuses = conn.execute(
                text("SELECT status FROM load_log WHERE source='fba_fee_ingestor'")
            ).fetchall()
            assert len(statuses) == 1
            assert statuses[0].status == "success"
    finally:
        engine.dispose()
