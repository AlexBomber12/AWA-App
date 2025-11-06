import os

import pytest

from services.etl import load_csv as lc

pytestmark = pytest.mark.integration


def test_import_from_minio_uri_monkeypatched(csv_file_factory, ensure_test_generic_table, pg_engine, monkeypatch):
    os.environ["TESTING"] = "1"
    local = csv_file_factory(
        headers=["ASIN", "qty", "price"],
        rows=[{"ASIN": "A1", "qty": 1, "price": 10.0}],
        name="minio.csv",
    )
    s3_uri = "s3://bucket/key/minio.csv"

    def fake_open_uri(uri: str):
        assert uri == s3_uri
        return local

    monkeypatch.setattr(lc, "_open_uri", fake_open_uri, raising=True)

    if hasattr(lc, "import_uri"):
        lc.import_uri(s3_uri, dialect="test_generic")
    else:
        p = lc._open_uri(s3_uri)
        lc.import_file(str(p), dialect="test_generic")

    with pg_engine.connect() as c:
        count = c.execute("SELECT COUNT(*) FROM test_generic_raw").scalar_one()
    assert count == 1
