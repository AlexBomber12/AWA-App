from sqlalchemy import create_engine, text
from services.common.dsn import build_dsn
import pytest

pytestmark = pytest.mark.integration


def test_roi_after_returns(pg_pool):
    engine = create_engine(build_dsn(sync=True))
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO vendors(id, name) VALUES (1,'ACME') ON CONFLICT DO NOTHING"))
        conn.execute(text("INSERT INTO products(asin) VALUES ('A1')"))
        conn.execute(text("INSERT INTO vendor_prices(vendor_id, sku, cost) VALUES (1,'A1',10)"))
        conn.execute(
            text(
                "INSERT INTO fees_raw(asin, fulfil_fee, referral_fee, storage_fee, currency) VALUES ('A1',1,1,1,'EUR')"
            )
        )
        conn.execute(text("INSERT INTO keepa_offers(asin, buybox_price) VALUES ('A1',20)"))
        conn.execute(
            text(
                "INSERT INTO returns_raw(asin, order_id, return_reason, return_date, qty, refund_amount, currency) VALUES ('A1','O1','damaged','2024-06-01',1,5,'EUR')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO reimbursements_raw(asin, reimb_id, reimb_date, qty, amount, currency, reason_code) VALUES ('A1','R1','2024-06-02',1,3,'EUR','goodwill')"
            )
        )
        conn.execute(text("REFRESH MATERIALIZED VIEW v_refund_totals"))
        conn.execute(text("REFRESH MATERIALIZED VIEW v_reimb_totals"))

    with engine.connect() as conn:
        roi = conn.execute(text("SELECT roi_pct FROM v_roi_full WHERE asin='A1'"))
        roi_val = roi.scalar()
    assert roi_val == 50.0
