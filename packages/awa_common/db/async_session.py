from __future__ import annotations

from collections.abc import AsyncGenerator
from threading import Lock
from typing import Any

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from awa_common.dsn import build_dsn
from awa_common.settings import settings

_ENGINE: AsyncEngine | None = None
_SESSIONMAKER: async_sessionmaker[AsyncSession] | None = None
_INIT_LOCK = Lock()


def _ensure_async_driver(raw: str) -> str:
    """Force Postgres URLs to use the asyncpg driver."""
    try:
        url = make_url(raw)
    except Exception:
        return raw
    driver = url.drivername
    if driver.startswith("postgresql+"):
        base, _, _ = driver.partition("+")
        driver = f"{base}+asyncpg"
    elif driver in {"postgresql", "postgres"}:
        driver = "postgresql+asyncpg"
    return str(url.set(drivername=driver))


def _resolve_dsn(explicit: str | None) -> str:
    if explicit:
        return _ensure_async_driver(explicit)
    try:
        value = settings.POSTGRES_DSN
    except Exception:
        value = None
    if value:
        return _ensure_async_driver(str(value))
    return build_dsn(sync=False)


def init_async_engine(dsn: str | None = None, **engine_kwargs: Any) -> AsyncEngine:
    """Create the shared AsyncEngine if it does not already exist."""
    global _ENGINE, _SESSIONMAKER
    with _INIT_LOCK:
        if _ENGINE is not None:
            return _ENGINE
        url = _resolve_dsn(dsn)
        kwargs: dict[str, Any] = {"pool_pre_ping": True, "future": True}
        kwargs.update(engine_kwargs)
        app_cfg = getattr(settings, "app", None)
        is_testing = bool(app_cfg.testing if app_cfg else getattr(settings, "TESTING", False))
        if is_testing:
            kwargs.setdefault("poolclass", NullPool)
        engine = create_async_engine(url, **kwargs)
        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        _ENGINE = engine
        _SESSIONMAKER = session_factory
        return engine


def get_async_engine() -> AsyncEngine:
    """Return the shared AsyncEngine, creating it lazily when required."""
    if _ENGINE is None:
        return init_async_engine()
    return _ENGINE


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the async session factory."""
    if _SESSIONMAKER is None:
        init_async_engine()
    assert _SESSIONMAKER is not None  # for type checkers
    return _SESSIONMAKER


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency that yields an AsyncSession."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_async_engine() -> None:
    """Dispose the shared AsyncEngine and reset session state."""
    global _ENGINE, _SESSIONMAKER
    engine = _ENGINE
    _ENGINE = None
    _SESSIONMAKER = None
    if engine is not None:
        await engine.dispose()


__all__ = [
    "dispose_async_engine",
    "get_async_engine",
    "get_async_session",
    "get_sessionmaker",
    "init_async_engine",
]
