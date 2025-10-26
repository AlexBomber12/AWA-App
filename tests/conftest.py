from __future__ import annotations

import asyncio
import importlib
import os
import time
from pathlib import Path

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
if importlib.util.find_spec("asyncpg") is not None:
    import asyncpg
    from asyncpg import create_pool
else:  # pragma: no cover - exercised only when asyncpg is missing
    asyncpg = None
    create_pool = None

if importlib.util.find_spec("sqlalchemy") is not None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
else:  # pragma: no cover - exercised only when sqlalchemy is missing
    create_engine = None
    sessionmaker = None

from awa_common.dsn import build_dsn


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test that requires live Postgres"
    )


def _db_available() -> bool:
    if asyncpg is None:
        return False

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
    markexpr = config.getoption("-m")
    if markexpr and "integration" not in markexpr:
        return
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

# Set environment variables for build_dsn function
os.environ.setdefault("PG_HOST", PG_HOST)
os.environ.setdefault("PG_PORT", PG_PORT)
os.environ.setdefault("PG_USER", PG_USER)
os.environ.setdefault("PG_PASSWORD", PG_PASSWORD)
os.environ.setdefault("PG_DATABASE", PG_DATABASE)


@pytest.fixture(scope="session", autouse=True)
def _set_db_url():
    sync_url = build_dsn(sync=True)
    os.environ["DATABASE_URL"] = sync_url
    os.environ["PG_ASYNC_DSN"] = sync_url.replace("+psycopg", "")


@pytest.fixture(scope="session", autouse=True)
def migrate_db(_set_db_url, request):
    """Ensure the database schema is present for tests."""
    markexpr = request.config.getoption("-m")
    if markexpr and "integration" not in markexpr:
        return
    if asyncpg is None:
        pytest.skip("asyncpg not installed – integration tests skipped")

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
    if asyncpg is None:
        pytest.skip("asyncpg not installed – integration tests skipped")

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
    if create_pool is None:
        pytest.skip("asyncpg not installed – integration tests skipped")

    async_dsn = os.getenv("PG_ASYNC_DSN") or build_dsn(sync=False)
    pool = await create_pool(dsn=async_dsn)
    yield pool
    await pool.close()


@pytest.fixture()
def db_engine(_set_db_url, _migrate):
    if create_engine is None:
        pytest.skip("sqlalchemy not installed – integration tests skipped")

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

    with TestClient(app) as client:  # type: ignore[arg-type]
        yield client


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


@pytest.fixture(autouse=True)
def _fast_sleep_all(monkeypatch, request):
    # Opt-out with @pytest.mark.real_sleep on tests that must keep true timing
    if request.node.get_closest_marker("real_sleep"):
        return

    async def _fast_asyncio_sleep(_delay=0, *_a, **_k):
        return None

    def _fast_time_sleep(_delay=0):
        return None

    monkeypatch.setattr(asyncio, "sleep", _fast_asyncio_sleep, raising=True)
    monkeypatch.setattr(time, "sleep", _fast_time_sleep, raising=True)


@pytest.fixture(autouse=True)
def _api_fast_startup_global(monkeypatch, request):
    """Fast lifespan for API tests using TestClient(main.app).
    Always no-op FastAPILimiter & Redis; only skip _wait_for_db patch if a test
    needs the real DB retry loop via @pytest.mark.needs_wait_for_db.
    Opt-out of the whole shim with @pytest.mark.real_lifespan.
    """
    if request.node.get_closest_marker("real_lifespan"):
        return

    # 1) limiter no-ops (always)
    try:
        import fastapi_limiter

        async def _noop_async(*_a, **_k):
            return None

        class _FakeLimiterRedis:
            async def evalsha(self, *_a, **_k):
                return 0

            async def script_load(self, *_a, **_k):
                return "noop"

        monkeypatch.setattr(
            fastapi_limiter.FastAPILimiter, "init", _noop_async, raising=True
        )
        monkeypatch.setattr(
            fastapi_limiter.FastAPILimiter, "close", _noop_async, raising=False
        )
        monkeypatch.setattr(
            fastapi_limiter.FastAPILimiter, "redis", _FakeLimiterRedis(), raising=False
        )
        monkeypatch.setattr(
            fastapi_limiter.FastAPILimiter, "lua_sha", "noop", raising=False
        )
    except Exception:
        pass

    # 2) Redis no-op (always)
    try:
        import redis.asyncio as aioredis

        class _FakeRedis:
            async def ping(self):
                return True

            async def aclose(self):
                return None

        monkeypatch.setattr(
            aioredis, "from_url", lambda *_a, **_k: _FakeRedis(), raising=True
        )
    except Exception:
        pass

    # 3) Only patch _wait_for_db if the test does NOT request the real loop
    if not request.node.get_closest_marker("needs_wait_for_db"):
        try:
            import services.api.main as main

            async def _noop_wait():
                return None

            monkeypatch.setattr(main, "_wait_for_db", _noop_wait, raising=True)
        except Exception:
            pass
