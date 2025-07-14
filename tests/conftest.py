import os
from pathlib import Path

import pytest
from asyncpg import create_pool

from tests.utils import run_migrations
from services.common.dsn import build_dsn

os.environ.setdefault("ENABLE_LIVE", "0")
os.environ.setdefault("TESTING", "1")

DATA_DIR = Path(os.getenv("DATA_DIR", "/tmp")) / "awa-data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DATA_DIR"] = str(DATA_DIR)


PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "pass")
PG_DATABASE = os.getenv("PG_DATABASE", "awa")


@pytest.fixture(autouse=True)
def _set_db_url():
    os.environ["DATABASE_URL"] = build_dsn(sync=True)


@pytest.fixture
async def pg_pool(_set_db_url):
    async_dsn = os.getenv("PG_ASYNC_DSN") or build_dsn(sync=False)
    pool = await create_pool(dsn=async_dsn)
    await run_migrations()
    yield pool
    await pool.close()


@pytest.fixture
def api_client(pg_pool):
    from fastapi.testclient import TestClient
    from services.api.main import app

    return TestClient(app)  # type: ignore[arg-type]


@pytest.fixture
def data_dir() -> Path:
    return DATA_DIR


@pytest.fixture()
def sample_xlsx(tmp_path: Path) -> Path:
    """Return Path to a temporary XLSX converted from existing CSV."""
    pd = pytest.importorskip("pandas")
    csv_path = Path("tests/fixtures/sample_prices.csv")
    df = pd.read_csv(csv_path)
    xls_path = tmp_path / "sample_prices.xlsx"
    df.to_excel(xls_path, index=False)
    return xls_path
