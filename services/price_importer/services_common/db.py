import asyncio
from collections.abc import Callable
from typing import cast
from urllib.parse import urlparse, urlunparse

from asyncpg import Pool, create_pool
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from awa_common.dsn import build_dsn as _raw_build_dsn
from awa_common.utils.env import env_bool

BuildDsnFn = Callable[..., str]
_build_dsn: BuildDsnFn = cast(BuildDsnFn, _raw_build_dsn)


def build_sqlalchemy_url() -> str:
    """Return Postgres URL for SQLAlchemy engines."""
    return _build_dsn(sync=True)


def build_asyncpg_dsn() -> str:
    """Return DSN suitable for asyncpg (without driver suffix)."""
    url = urlparse(_build_dsn(sync=True))
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


def refresh_mvs(conn: Engine | Connection) -> None:
    """Refresh materialized views, using CONCURRENTLY when safe."""
    if isinstance(conn, Engine):
        with conn.begin() as connection:
            refresh_mvs(connection)
        return

    live = env_bool("ENABLE_LIVE", default=True)
    idx_exists = bool(
        conn.execute(text("SELECT 1 FROM pg_indexes WHERE indexname = 'ix_v_refund_totals_pk'")).scalar()
    ) and bool(conn.execute(text("SELECT 1 FROM pg_indexes WHERE indexname = 'ix_v_reimb_totals_pk'")).scalar())
    option = " CONCURRENTLY" if live and idx_exists else ""
    conn.execute(text(f"REFRESH MATERIALIZED VIEW{option} v_refund_totals"))
    conn.execute(text(f"REFRESH MATERIALIZED VIEW{option} v_reimb_totals"))
