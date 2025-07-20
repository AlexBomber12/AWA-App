import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


def test_roi_view_calculation(migrated_session):
    with migrated_session.begin():
        migrated_session.execute(
            text("INSERT INTO vendors(id, name) VALUES (1,'test')")
        )
        migrated_session.execute(
            text("INSERT INTO products(asin, title) VALUES ('S1','Test')")
        )
        migrated_session.execute(
            text(
                "INSERT INTO vendor_prices(vendor_id, sku, cost, updated_at) VALUES (1,'S1',5,'2024-01-01')"
            )
        )
        migrated_session.execute(
            text("INSERT INTO keepa_offers(asin, buybox_price) VALUES ('S1',12)")
        )
        migrated_session.execute(
            text(
                "INSERT INTO fees_raw(asin, fulfil_fee, referral_fee, storage_fee, currency, updated_at)"
                " VALUES ('S1',1,1,1,'EUR','2024-01-01')"
            )
        )

    roi = migrated_session.execute(
        text("SELECT roi_pct FROM v_roi_full WHERE asin='S1'")
    ).scalar()
    expected = round(100 * (12 - 5 - 1 - 1 - 1) / 5, 1)
    assert roi == expected

    roi_view = migrated_session.execute(
        text("SELECT roi_pct FROM roi_view WHERE asin='S1'")
    ).scalar()
    assert roi_view == expected
