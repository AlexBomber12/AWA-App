import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from awa_common.dsn import build_dsn
from etl.load_csv import import_file

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not set"),
]


def test_idempotent_load(tmp_path):
    csv = Path("tests/fixtures/sample_returns.csv")

    res1 = import_file(str(csv))
    assert res1["status"] == "success"
    res2 = import_file(str(csv))
    assert res2["status"] == "skipped"
    res3 = import_file(str(csv), force=True)
    assert res3["status"] == "success"

    engine = create_engine(build_dsn(sync=True))
    with engine.connect() as conn:
        statuses = (
            conn.execute(
                text(
                    "SELECT status FROM load_log WHERE source='ingest.import_file' AND idempotency_key=:k ORDER BY id"
                ),
                {"k": res1["idempotency_key"]},
            )
            .scalars()
            .all()
        )
    assert statuses.count("success") >= 1
    assert statuses.count("skipped") >= 1
    engine.dispose()
