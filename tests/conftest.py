import os
import tempfile
import pathlib
import subprocess
import pytest
import site
import sys

import time
from pathlib import Path

os.environ.setdefault("ENABLE_LIVE", "0")
from services.common.db_url import build_url
from sqlalchemy import create_engine
from services.common import Base

DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", tempfile.gettempdir())) / "awa-data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DATA_DIR"] = str(DATA_DIR)

# ensure real fastapi package is used
site_pkg = site.getsitepackages()[0]
if sys.path[0] != site_pkg:
    sys.path.insert(0, site_pkg)
sys.modules.pop("fastapi", None)
from fastapi.testclient import TestClient  # noqa: E402
from services.api.main import app  # noqa: E402


def _wait_for_db() -> None:
    url = build_url(async_=True)
    if url.startswith("sqlite"):
        return
    for _ in range(10):
        try:
            rc = subprocess.run(
                [
                    "pg_isready",
                    "-h",
                    os.getenv("PG_HOST", "postgres"),
                    "-p",
                    "5432",
                    "-U",
                    os.getenv("PG_USER", "postgres"),
                ],
                capture_output=True,
            ).returncode
        except FileNotFoundError:
            return
        if rc == 0:
            return
        time.sleep(1)
    raise RuntimeError("postgres not ready")


def pytest_sessionstart(session):
    _wait_for_db()
    url = build_url(async_=True)
    if url.startswith("sqlite"):
        path = url.split("///", 1)[1]
        if os.path.exists(path):
            os.remove(path)
    subprocess.run(
        ["alembic", "upgrade", "head"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)  # type: ignore[arg-type]


@pytest.fixture
def data_dir() -> Path:
    return DATA_DIR


@pytest.fixture()
def sample_xlsx(tmp_path: Path) -> Path:
    """Return Path to a temporary XLSX converted from existing CSV."""
    import pandas as pd

    csv_path = Path("tests/fixtures/sample_prices.csv")
    df = pd.read_csv(csv_path)
    xls_path = tmp_path / "sample_prices.xlsx"
    df.to_excel(xls_path, index=False)
    return xls_path


@pytest.fixture(autouse=True, scope="session")
def create_tables():
    url = build_url(async_=False)
    if url.startswith("sqlite"):
        engine = create_engine(url)
        Base.metadata.create_all(engine)
        with engine.begin() as conn:
            conn.exec_driver_sql(
                """
                CREATE TABLE IF NOT EXISTS keepa_offers (
                    asin TEXT PRIMARY KEY,
                    buybox_price NUMERIC(10,2)
                );
                """
            )
            conn.exec_driver_sql(
                """
                CREATE TABLE IF NOT EXISTS fees_raw (
                    asin TEXT PRIMARY KEY,
                    fulfil_fee NUMERIC(10,2) NOT NULL,
                    referral_fee NUMERIC(10,2) NOT NULL,
                    storage_fee NUMERIC(10,2) NOT NULL DEFAULT 0,
                    currency CHAR(3) NOT NULL DEFAULT '€',
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.exec_driver_sql(
                """
                CREATE VIEW IF NOT EXISTS v_roi_full AS
                SELECT
                  p.asin,
                  (SELECT cost FROM vendor_prices vp WHERE vp.sku = p.asin ORDER BY vp.updated_at DESC LIMIT 1) AS cost,
                  f.fulfil_fee,
                  f.referral_fee,
                  f.storage_fee,
                  k.buybox_price,
                  ROUND(
                    100 * (
                      k.buybox_price
                      - (SELECT cost FROM vendor_prices vp WHERE vp.sku = p.asin ORDER BY vp.updated_at DESC LIMIT 1)
                      - f.fulfil_fee
                      - f.referral_fee
                      - f.storage_fee
                    ) / k.buybox_price,
                  2) AS roi_pct
                FROM products p
                JOIN keepa_offers k  ON k.asin = p.asin
                JOIN fees_raw    f  ON f.asin = p.asin;
                """
            )
        yield
        Base.metadata.drop_all(engine)
        with engine.begin() as conn:
            conn.exec_driver_sql("DROP VIEW IF EXISTS v_roi_full")
    else:
        yield
