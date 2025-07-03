import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/awa.db")

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    echo=False,
)

AsyncSession = async_sessionmaker(engine, expire_on_commit=False)
