import asyncio
import os
from pathlib import Path

import pytest
from asyncpg import create_pool
from pytest_postgresql import factories

from tests.utils import run_migrations

os.environ.setdefault("ENABLE_LIVE", "0")
os.environ.setdefault("TESTING", "1")

DATA_DIR = Path(os.getenv("DATA_DIR", "/tmp")) / "awa-data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DATA_DIR"] = str(DATA_DIR)

# pass load=[] so the plugin does not iterate over None
postgres_proc = factories.postgresql_proc(user="postgres", load=[])
postgres = factories.postgresql("postgres_proc")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def _set_db_url(postgres):
    try:
        host = postgres.host
        port = postgres.port
    except AttributeError:
        host = postgres.info.host
        port = postgres.info.port
    url = f"postgresql+psycopg://postgres:pass@{host}:{port}/tests"
    os.environ["DATABASE_URL"] = url


@pytest.fixture
async def pg_pool(_set_db_url):
    pool = await create_pool(dsn=os.environ["DATABASE_URL"])
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
