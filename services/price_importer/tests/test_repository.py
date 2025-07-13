from sqlalchemy import create_engine
from services.price_importer.repository import Repository


def test_upsert_and_vendor(tmp_path):
    db = tmp_path / "db.sqlite"
    engine = create_engine(f"sqlite:///{db}")
    from services.price_importer.common import Base

    Base.metadata.create_all(engine)
    repo = Repository(engine)
    vendor_id = repo.ensure_vendor("ACME")
    inserted, updated = repo.upsert_prices(vendor_id, [{"sku": "A1", "cost": 1.0}])
    assert inserted == 1
    inserted, updated = repo.upsert_prices(vendor_id, [{"sku": "A1", "cost": 2.0}])
    assert updated == 1
