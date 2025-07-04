from typing import AsyncGenerator

import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    if os.getenv("ENABLE_LIVE") == "0":
        DATABASE_URL = "sqlite+aiosqlite:///data/awa.db"
    else:
        raise RuntimeError("DATABASE_URL environment variable required")

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    echo=False,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
