import asyncio
import os
from asyncpg import create_pool, Pool


async def create_pg_pool() -> Pool:
    url = os.environ["DATABASE_URL"]
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
