import asyncio
import os
import sys
import subprocess
import asyncpg


async def wait_for_db(url: str) -> None:
    delay = 0.3
    for _ in range(10):
        try:
            conn = await asyncpg.connect(url)
            await conn.execute("SELECT 1")
            await conn.close()
            subprocess.run(["alembic", "upgrade", "head"], check=True)
            return
        except Exception:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 3)
    raise RuntimeError("Database not available")


if __name__ == "__main__":
    dsn = os.environ.get("DATABASE_URL")
    asyncio.run(wait_for_db(dsn))
    os.execvp(sys.argv[1], sys.argv[1:])
