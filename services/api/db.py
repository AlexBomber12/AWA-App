import os
from typing import AsyncGenerator

from awa_common.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Always derive the database URL from shared settings
DATABASE_URL = settings.DATABASE_URL

pool_kwargs = {}
if os.getenv("TESTING") == "1":
    pool_kwargs["poolclass"] = NullPool

engine = create_async_engine(
    DATABASE_URL, pool_pre_ping=True, future=True, echo=False, **pool_kwargs
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def dispose_engine() -> None:
    await engine.dispose()
