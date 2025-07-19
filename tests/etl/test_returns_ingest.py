import pytest
from sqlalchemy import create_engine, text

from etl import load_csv
from services.common.dsn import build_dsn

pytestmark = pytest.mark.integration


def test_returns_ingest(tmp_path, refresh_mvs):
    csv_path = tmp_path / "returns.csv"
    csv_path.write_text(
        "ASIN,Order ID,Return Reason,Return Date,Qty,Refund Amount,Currency\n"
        "A1,O1,Damaged,2024-06-01,1,5.00,EUR\n"
        "A2,O2,Customer,2024-06-02,1,3.00,EUR\n"
    )
    load_csv.main(["--source", str(csv_path), "--table", "auto"])

    engine = create_engine(build_dsn(sync=True))
    with engine.connect() as conn:
        cnt = conn.execute(text("SELECT count(*) FROM returns_raw")).scalar()
        status = conn.execute(
            text("SELECT status FROM load_log ORDER BY id DESC LIMIT 1")
        ).scalar()

    assert cnt == 2
    assert status == "success"
