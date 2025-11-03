from __future__ import annotations

import asyncio
import contextlib
import datetime
import importlib
import os
import random
import sys
import time
import types
from pathlib import Path
from typing import Any, Sequence

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
    "faker_seed",
    "env_overrides",
    "dummy_user_ctx",
    "fastapi_dep_overrides",
    "http_mock",
    "smtp_mock",
    "now_utc",
    "tmp_path_helpers",
    "_stub_prometheus_client",
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
from awa_common.settings import settings


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test that requires live Postgres")


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
    skip_integration = pytest.mark.skip(reason="Postgres not running – integration tests skipped")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


os.environ.setdefault("ENABLE_LIVE", "0")
os.environ.setdefault("TESTING", "1")

DATA_DIR = Path(os.getenv("DATA_DIR", "/tmp")) / "awa-data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DATA_DIR"] = str(DATA_DIR)


def _install_prometheus_stub() -> None:
    from tests.stubs import prometheus_client as stub

    mod = types.ModuleType("prometheus_client")
    mod.Counter = stub.Counter
    mod.Histogram = stub.Histogram
    mod.Gauge = stub.Gauge
    mod.Summary = stub.Summary
    mod.generate_latest = stub.generate_latest
    mod.start_http_server = stub.start_http_server
    mod.CONTENT_TYPE_LATEST = stub.CONTENT_TYPE_LATEST
    sys.modules["prometheus_client"] = mod


_install_prometheus_stub()


@pytest.fixture(autouse=True, scope="session")
def _stub_prometheus_client():
    """Provide a lightweight prometheus_client replacement during tests."""

    _install_prometheus_stub()

    for name in list(sys.modules):
        if name.endswith(".metrics") or name.endswith("services.worker.metrics"):
            module = sys.modules.get(name)
            if module is None:
                continue
            try:
                importlib.reload(module)  # nosec - test only
            except Exception:
                pass
    yield


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
    settings.DATABASE_URL = sync_url  # type: ignore[attr-defined]


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

        repo_root = Path(__file__).resolve().parent.parent
        cmd = [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "services/api/alembic.ini",
            "upgrade",
            "head",
        ]
        subprocess.check_call(cmd, cwd=repo_root)


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
        pytest.skip("Postgres not running – integration tests skipped", allow_module_level=True)
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

        monkeypatch.setattr(fastapi_limiter.FastAPILimiter, "init", _noop_async, raising=True)
        monkeypatch.setattr(fastapi_limiter.FastAPILimiter, "close", _noop_async, raising=False)
        monkeypatch.setattr(
            fastapi_limiter.FastAPILimiter, "redis", _FakeLimiterRedis(), raising=False
        )
        monkeypatch.setattr(fastapi_limiter.FastAPILimiter, "lua_sha", "noop", raising=False)
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

        monkeypatch.setattr(aioredis, "from_url", lambda *_a, **_k: _FakeRedis(), raising=True)
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


def _parse_utc_datetime(value: datetime.datetime | str) -> datetime.datetime:
    """Normalize user-specified datetimes to timezone-aware UTC values."""
    if isinstance(value, datetime.datetime):
        dt_value = value
    else:
        normalized = value.replace("Z", "+00:00")
        dt_value = datetime.datetime.fromisoformat(normalized)
    if dt_value.tzinfo is None:
        return dt_value.replace(tzinfo=datetime.UTC)
    return dt_value.astimezone(datetime.UTC)


@pytest.fixture
def faker_seed():
    """Seed common RNG providers for deterministic tests; override by calling."""

    def _apply(seed: int = 1337) -> int:
        random.seed(seed)
        try:  # Optional numpy seeding when available
            import numpy as np  # type: ignore[import-not-found]
        except Exception:
            pass
        else:
            np.random.seed(seed)  # type: ignore[union-attr]
        try:
            from faker import Faker  # type: ignore[import-not-found]
        except Exception:
            pass
        else:
            Faker.seed(seed)
        return seed

    _apply()
    return _apply


@pytest.fixture
def env_overrides(monkeypatch: pytest.MonkeyPatch):
    """Context manager to temporarily set or clear environment variables."""

    @contextlib.contextmanager
    def _override(**overrides: str | None):
        originals = {key: os.environ.get(key) for key in overrides}
        for key, value in overrides.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, str(value))
        try:
            yield
        finally:
            for key, original in originals.items():
                if original is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original

    return _override


@pytest.fixture
def dummy_user_ctx():
    """Return a factory that builds lightweight Principal objects for tests."""

    def _factory(
        roles: Sequence[str] | None = None,
        *,
        user_id: str = "test-user",
        email: str | None = "test@example.com",
    ):
        from services.api.security import Principal

        assigned = set(roles or [])
        if not assigned:
            assigned.add("viewer")
        return Principal(id=user_id, email=email, roles=assigned)

    return _factory


@pytest.fixture
def fastapi_dep_overrides():
    """Context manager that safely overrides FastAPI dependency wiring."""

    @contextlib.contextmanager
    def _override(app, **dependency_map):
        original = dict(getattr(app, "dependency_overrides", {}))
        app.dependency_overrides.update(dependency_map)
        try:
            yield app
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(original)

    return _override


@pytest.fixture
def http_mock(monkeypatch: pytest.MonkeyPatch):
    """HTTP transport stub that routes httpx traffic to queued canned responses."""

    try:
        import httpx
    except Exception:  # pragma: no cover - httpx is present in test envs
        httpx = None  # type: ignore[assignment]

    class _HttpMock:
        def __init__(self):
            self._routes: dict[tuple[str, str], list[dict[str, Any]]] = {}
            self.calls: list[dict[str, Any]] = []

        def add(
            self,
            method: str,
            url: str,
            *,
            status_code: int = 200,
            json: Any | None = None,
            text: str | None = None,
            headers: dict[str, str] | None = None,
            exc: Exception | type[Exception] | None = None,
        ) -> None:
            if httpx is None:
                raise RuntimeError("httpx is required for http_mock")
            key = (method.upper(), str(httpx.URL(url)))
            spec = {
                "status_code": status_code,
                "json": json,
                "text": text,
                "headers": headers or {},
                "exception": exc,
            }
            self._routes.setdefault(key, []).append(spec)

        def _handle(self, request: Any):
            if httpx is None:  # pragma: no cover
                raise RuntimeError("httpx is required for http_mock")
            key = (request.method.upper(), str(request.url))
            self.calls.append({"method": request.method.upper(), "url": str(request.url)})
            queue = self._routes.get(key)
            if not queue:
                raise AssertionError(f"Unexpected HTTP request: {request.method} {request.url}")
            spec = queue.pop(0)
            exc = spec.get("exception")
            if exc:
                raise exc if isinstance(exc, Exception) else exc()
            if spec.get("json") is not None:
                return httpx.Response(
                    spec["status_code"], json=spec["json"], headers=spec["headers"]
                )
            return httpx.Response(
                spec["status_code"],
                text=spec.get("text") or "",
                headers=spec["headers"],
            )

        @contextlib.contextmanager
        def use(self):
            if httpx is None:  # pragma: no cover
                raise RuntimeError("httpx is required for http_mock")

            transport = httpx.MockTransport(self._handle)

            class _PatchedClient(httpx.Client):
                def __init__(self, *args, **kwargs):
                    kwargs.setdefault("transport", transport)
                    super().__init__(*args, **kwargs)

            class _PatchedAsyncClient(httpx.AsyncClient):
                def __init__(self, *args, **kwargs):
                    kwargs.setdefault("transport", transport)
                    super().__init__(*args, **kwargs)

            with monkeypatch.context() as mp:
                mp.setattr(httpx, "Client", _PatchedClient, raising=True)
                mp.setattr(httpx, "AsyncClient", _PatchedAsyncClient, raising=True)
                yield self

    return _HttpMock()


@pytest.fixture
def smtp_mock(monkeypatch: pytest.MonkeyPatch):
    """Context manager that captures outbound SMTP traffic into an in-memory list."""

    import smtplib

    sent_messages: list[dict[str, Any]] = []

    class _DummySMTP:
        def __init__(self, host=None, port=None, **kwargs):
            self.host = host
            self.port = port
            self.kwargs = kwargs
            self.closed = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.quit()

        def sendmail(self, from_addr, to_addrs, msg, *_args, **_kwargs):
            recipients = list(to_addrs) if isinstance(to_addrs, list | tuple | set) else [to_addrs]
            sent_messages.append({"from": from_addr, "to": recipients, "message": msg})
            return {}

        def send_message(self, message, from_addr=None, to_addrs=None, *_args, **_kwargs):
            if hasattr(message, "as_string"):
                payload = message.as_string()
            else:
                payload = str(message)
            if to_addrs is None and hasattr(message, "get_all"):
                recipients = message.get_all("To", [])
            else:
                recipients = to_addrs or []
            if isinstance(recipients, str):
                recipients = [recipients]
            elif not isinstance(recipients, list):
                recipients = list(recipients)
            sender = from_addr
            if sender is None and hasattr(message, "get"):
                sender = message.get("From")
            sent_messages.append({"from": sender, "to": recipients, "message": payload})
            return {}

        def quit(self):
            self.closed = True
            return {}

    @contextlib.contextmanager
    def _patch():
        sent_messages.clear()
        with monkeypatch.context() as mp:
            mp.setattr(smtplib, "SMTP", _DummySMTP, raising=True)
            mp.setattr(smtplib, "SMTP_SSL", _DummySMTP, raising=True)
            yield sent_messages

    return _patch


@pytest.fixture
def now_utc(monkeypatch: pytest.MonkeyPatch):
    """Patch a time provider to return a fixed UTC datetime without external libs."""

    def _freeze(target: str, value: datetime.datetime | str = "2024-01-01T00:00:00Z"):
        fixed = _parse_utc_datetime(value)

        def _stub(*_args, **_kwargs):
            return fixed

        monkeypatch.setattr(target, _stub, raising=False)
        return fixed

    return _freeze


@pytest.fixture
def tmp_path_helpers(tmp_path_factory: pytest.TempPathFactory):
    """Helpers for scratch files that are always written outside the repo tree."""

    base_dir = tmp_path_factory.mktemp("awa-files")

    class _TmpHelpers:
        def __init__(self, root: Path):
            self.root = root

        def make_file(self, relative: str, contents: str = "", *, encoding: str = "utf-8") -> Path:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding=encoding)
            return path

        def make_dir(self, relative: str) -> Path:
            path = self.root / relative
            path.mkdir(parents=True, exist_ok=True)
            return path

        def copy_fixture(self, relative: str) -> Path:
            source = Path("tests/fixtures") / relative
            if not source.exists():
                raise FileNotFoundError(f"Missing fixture: tests/fixtures/{relative}")
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
            return destination

    return _TmpHelpers(base_dir)
