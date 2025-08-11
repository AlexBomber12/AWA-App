from importlib import import_module
from pathlib import Path

from sqlalchemy import text

from services.price_importer.repository import Repository

imp = import_module("services.price_importer.import")


def test_price_importer_cli(tmp_path, monkeypatch):
    csv = Path("tests/fixtures/sample_prices.csv")
    db = tmp_path / "test.db"
    database_url = f"sqlite:///{db}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    assert imp.main([str(csv), "--vendor", "acme"]) == 0

    # Use the same DATABASE_URL that the import used
    repo = Repository()
    with repo.engine.connect() as conn:
        cnt = conn.execute(text("SELECT count(*) FROM vendor_prices")).scalar()
    assert cnt > 0
