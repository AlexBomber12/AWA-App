import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


def _build_database_url() -> str:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    if user and password and db:
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/awa.db")


DATABASE_URL = _build_database_url()

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    echo=False,
)

AsyncSession = async_sessionmaker(engine, expire_on_commit=False)
