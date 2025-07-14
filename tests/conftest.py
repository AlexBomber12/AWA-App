import asyncio
import os
from pathlib import Path

import pytest
from asyncpg import create_pool
from testcontainers.postgres import PostgresContainer

from tests.utils import run_migrations

os.environ.setdefault("ENABLE_LIVE", "0")
os.environ.setdefault("TESTING", "1")

DATA_DIR = Path(os.getenv("DATA_DIR", "/tmp")) / "awa-data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DATA_DIR"] = str(DATA_DIR)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def pg_container(event_loop):
    with PostgresContainer("postgres:15").with_bind_ports(5432, 5432) as pg:
        url = pg.get_connection_url()
        os.environ["DATABASE_URL"] = url.replace("postgresql://", "postgresql+asyncpg://")
        os.environ["PG_USER"] = pg.USERNAME
        os.environ["PG_PASSWORD"] = pg.PASSWORD
        os.environ["PG_HOST"] = pg.get_container_host_ip()
        os.environ["PG_PORT"] = pg.get_exposed_port(pg.port)
        os.environ["PG_DATABASE"] = pg.DBNAME
        yield pg


@pytest.fixture(scope="session")
async def pg_pool(pg_container):
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
