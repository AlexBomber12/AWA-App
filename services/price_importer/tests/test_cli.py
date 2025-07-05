from pathlib import Path
import sqlite3
import os
from importlib import import_module

importer = import_module("services.price_importer.import")


def test_cli_import(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE", "0")
    data_dir = Path(os.environ["DATA_DIR"])
    sample = Path("tests/fixtures/sample_prices.csv")
    res = importer.main([str(sample), "--vendor", "ACME GmbH"])
    assert res == 0
    conn = sqlite3.connect(data_dir / "awa.db")
    rows = conn.execute("SELECT count(*) FROM vendor_prices").fetchone()[0]
    assert rows > 0
