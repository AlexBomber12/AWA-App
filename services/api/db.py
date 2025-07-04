from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from services.common.db_url import build_db_url

DATABASE_URL = build_db_url()

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
