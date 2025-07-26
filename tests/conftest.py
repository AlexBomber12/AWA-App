from __future__ import annotations

import asyncio
import os
from pathlib import Path

import asyncpg
import pytest

__all__ = [
    "pytest_configure",
    "_db_available",
    "pytest_collection_modifyitems",
    "_set_db_url",
    "migrate_db",
    "pg_pool",
    "db_engine",
    "refresh_mvs",
    "api_client",
    "data_dir",
    "sample_xlsx",
    "migrated_session",
]
from asyncpg import create_pool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.common.dsn import build_dsn


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test that requires live Postgres"
    )


def _db_available() -> bool:
    async def _check() -> None:
        conn = await asyncpg.connect(
            dsn=os.getenv("PG_ASYNC_DSN", build_dsn(sync=False)), timeout=1
        )
        await conn.close()

    try:
        asyncio.run(_check())
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    if _db_available():
        return
    skip_integration = pytest.mark.skip(
        reason="Postgres not running – integration tests skipped"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


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


@pytest.fixture(scope="session", autouse=True)
def _set_db_url():
    sync_url = build_dsn(sync=True)
    os.environ["DATABASE_URL"] = sync_url
    os.environ["PG_ASYNC_DSN"] = sync_url.replace("+psycopg", "")


@pytest.fixture(scope="session", autouse=True)
def migrate_db(_set_db_url):
    """Ensure the database schema is present for tests."""
    if os.getenv("TESTING") != "1" or not _db_available():
        return

    async def _has_table() -> bool:
        dsn = os.getenv("PG_ASYNC_DSN") or build_dsn(sync=False)
        conn = await asyncpg.connect(dsn)
        try:
            return bool(await conn.fetchval("SELECT to_regclass('products')"))
        finally:
            await conn.close()

    if not asyncio.run(_has_table()):
        import subprocess

        subprocess.check_call(
            ["alembic", "-c", "services/api/alembic.ini", "upgrade", "head"]
        )


@pytest.fixture(scope="session")
async def _migrate(_set_db_url):
    dsn = os.getenv("PG_ASYNC_DSN") or build_dsn(sync=False)
    for _ in range(30):
        try:
            conn = await asyncpg.connect(dsn)
            await conn.close()
            break
        except Exception:
            await asyncio.sleep(2)
    else:
        pytest.skip(
            "Postgres not running – integration tests skipped", allow_module_level=True
        )
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config("services/api/alembic.ini"), "head")


@pytest.fixture
async def pg_pool(_set_db_url, _migrate):
    async_dsn = os.getenv("PG_ASYNC_DSN") or build_dsn(sync=False)
    pool = await create_pool(dsn=async_dsn)
    yield pool
    await pool.close()


@pytest.fixture()
def db_engine(_set_db_url, _migrate):
    engine = create_engine(build_dsn(sync=True))
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def refresh_mvs(db_engine):
    with db_engine.begin() as conn:
        conn.execute("REFRESH MATERIALIZED VIEW v_refund_totals")
        conn.execute("REFRESH MATERIALIZED VIEW v_reimb_totals")
    yield


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


@pytest.fixture()
def migrated_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
