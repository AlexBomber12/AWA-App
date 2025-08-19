import os

import pytest

from services.etl import load_csv as lc

pytestmark = pytest.mark.integration


def test_large_with_duplicates(large_csv_factory, ensure_test_generic_table, pg_engine):
    os.environ["TESTING"] = "1"
    base = large_csv_factory(5000, name="base.csv")
    dup = large_csv_factory(2500, name="dup.csv")
    lc.import_file(str(base), dialect="test_generic")
    lc.import_file(str(dup), dialect="test_generic")
    with pg_engine.connect() as c:
        total = c.execute("SELECT COUNT(*) FROM test_generic_raw").scalar_one()
        changed = c.execute(
            """
            SELECT COUNT(*) FROM test_generic_raw t
            JOIN (
                SELECT 'A00000' AS asin
            ) x ON t."ASIN" = x.asin
            """
        ).scalar_one()
    assert total == 5000
    assert changed == 1
