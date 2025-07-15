import asyncio
from urllib.parse import urlparse, urlunparse
from asyncpg import create_pool, Pool

from .dsn import build_dsn


def build_sqlalchemy_url() -> str:
    """Return Postgres URL for SQLAlchemy engines."""
    return build_dsn(sync=True)


def build_asyncpg_dsn() -> str:
    """Return DSN suitable for asyncpg (without driver suffix)."""
    url = urlparse(build_dsn(sync=True))
    return urlunparse(
        (
            "postgresql",
            f"{url.username}:{url.password}@{url.hostname}:{url.port}",
            url.path,
            "",
            "",
            "",
        )
    )


async def create_pg_pool() -> Pool:
    url = build_asyncpg_dsn()
    delay = 0.5
    for attempt in range(3):
        try:
            return await create_pool(dsn=url)
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(delay)
            delay *= 2
    raise RuntimeError("Could not connect to Postgres")
