from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from threading import Lock
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from awa_common.dsn import build_dsn
from awa_common.metrics import record_db_pool_near_limit, record_db_pool_usage
from awa_common.settings import settings

_ENGINE: AsyncEngine | None = None
_SESSIONMAKER: async_sessionmaker[AsyncSession] | None = None
_INIT_LOCK = Lock()
_POOL_WARNINGS: dict[str, float] = {}
logger = logging.getLogger(__name__)


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
    db_cfg = getattr(settings, "db", None)
    if db_cfg and getattr(db_cfg, "async_dsn", None):
        return _ensure_async_driver(str(db_cfg.async_dsn))
    try:
        value = settings.POSTGRES_DSN
    except Exception:
        value = None
    if value:
        return _ensure_async_driver(str(value))
    return build_dsn(sync=False)


def _install_pool_monitor(
    engine: AsyncEngine,
    *,
    pool_label: str,
    pool_size: int,
    max_overflow: int,
    warn_pct: float,
    warn_interval_s: float,
) -> None:
    pool = getattr(engine.sync_engine, "pool", None)
    if pool is None or not hasattr(pool, "checkedout"):
        return

    capacity = max(int(pool_size) + max(int(max_overflow), 0), 1)
    warn_threshold = capacity * max(0.0, min(warn_pct, 1.0))

    def _record_usage() -> None:
        in_use = int(pool.checkedout()) if hasattr(pool, "checkedout") else 0
        overflow = int(pool.overflow()) if hasattr(pool, "overflow") else 0
        record_db_pool_usage(pool_label, in_use=in_use, capacity=capacity, overflow=overflow)
        if warn_threshold <= 0:
            return
        if in_use < warn_threshold:
            return
        now = time.monotonic()
        last = _POOL_WARNINGS.get(pool_label, 0.0)
        if now - last < max(warn_interval_s, 0.0):
            return
        _POOL_WARNINGS[pool_label] = now
        logger.warning(
            "db_pool.near_limit",
            extra={
                "pool": pool_label,
                "in_use": in_use,
                "capacity": capacity,
                "pool_size": pool_size,
                "max_overflow": max_overflow,
            },
        )
        record_db_pool_near_limit(pool_label)

    @event.listens_for(engine.sync_engine, "checkout")
    def _on_checkout(*_args: Any, **_kwargs: Any) -> None:  # pragma: no cover - lightweight hooks
        _record_usage()

    @event.listens_for(engine.sync_engine, "checkin")
    def _on_checkin(*_args: Any, **_kwargs: Any) -> None:  # pragma: no cover - lightweight hooks
        _record_usage()

    _record_usage()


def init_async_engine(dsn: str | None = None, **engine_kwargs: Any) -> AsyncEngine:
    """Create the shared AsyncEngine if it does not already exist."""
    global _ENGINE, _SESSIONMAKER
    with _INIT_LOCK:
        if _ENGINE is not None:
            return _ENGINE
        url = _resolve_dsn(dsn)
        kwargs: dict[str, Any] = {"pool_pre_ping": True, "future": True}
        kwargs.update(engine_kwargs)
        db_cfg = getattr(settings, "db", None)
        app_cfg = getattr(settings, "app", None)
        is_testing = bool(app_cfg.testing if app_cfg else getattr(settings, "TESTING", False))
        if is_testing:
            kwargs.setdefault("poolclass", NullPool)
        else:
            if db_cfg:
                kwargs.setdefault("pool_size", int(db_cfg.pool_size))
                kwargs.setdefault("max_overflow", int(db_cfg.max_overflow))
                kwargs.setdefault("pool_timeout", float(db_cfg.pool_timeout))
            else:
                kwargs.setdefault("pool_timeout", float(getattr(settings, "ASYNC_DB_POOL_TIMEOUT", 30.0)))
        pool_size = int(kwargs.get("pool_size", getattr(db_cfg, "pool_size", 5)))
        max_overflow = int(kwargs.get("max_overflow", getattr(db_cfg, "max_overflow", 10)))
        warn_pct = float(getattr(db_cfg, "pool_warn_pct", getattr(settings, "DB_POOL_WARN_PCT", 0.85)))
        warn_pct = max(0.0, min(warn_pct, 1.0))
        warn_interval = float(
            getattr(db_cfg, "pool_warn_interval_s", getattr(settings, "DB_POOL_WARN_INTERVAL_S", 60.0))
        )
        pool_label = getattr(app_cfg, "service_name", getattr(settings, "SERVICE_NAME", "api"))
        engine = create_async_engine(url, **kwargs)
        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        if not is_testing and hasattr(engine, "sync_engine"):
            _install_pool_monitor(
                engine,
                pool_label=pool_label,
                pool_size=pool_size,
                max_overflow=max_overflow,
                warn_pct=warn_pct,
                warn_interval_s=warn_interval,
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
    _POOL_WARNINGS.clear()
    if engine is not None:
        await engine.dispose()


__all__ = [
    "dispose_async_engine",
    "get_async_engine",
    "get_async_session",
    "get_sessionmaker",
    "init_async_engine",
]
