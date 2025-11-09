from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from awa_common.db.async_session import (
    dispose_async_engine as dispose_engine,
    get_async_session as get_session,
    get_sessionmaker,
    init_async_engine,
)


def async_session() -> AsyncSession:
    """Backwards-compatible factory that lazily creates AsyncSession objects."""
    factory: async_sessionmaker[AsyncSession] = get_sessionmaker()
    return factory()


__all__ = [
    "async_session",
    "dispose_engine",
    "get_session",
    "get_sessionmaker",
    "init_async_engine",
]
