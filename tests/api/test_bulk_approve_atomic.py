from __future__ import annotations

import types

import pytest
from sqlalchemy import text

from awa_common.db.async_session import dispose_async_engine, get_sessionmaker, init_async_engine
from awa_common.dsn import build_dsn
from services.api.app.repositories import roi as roi_repo

pytestmark = pytest.mark.integration


async def _seed_products(pg_pool):
    async with pg_pool.acquire() as conn:  # type: ignore[attr-defined]
        await conn.execute("DELETE FROM products")
        await conn.execute(
            """
            INSERT INTO products(asin, title, category, weight_kg, status)
            VALUES
                ('A1','t1','cat',1,'pending'),
                ('A2','t2','cat',1,'pending')
            ON CONFLICT (asin) DO UPDATE SET status=EXCLUDED.status
            """
        )


@pytest.fixture
async def session_factory(pg_pool):
    init_async_engine(build_dsn(sync=False))
    factory = get_sessionmaker()
    try:
        yield factory
    finally:
        await dispose_async_engine()


@pytest.mark.asyncio
async def test_bulk_approve_happy_path(monkeypatch, pg_pool, session_factory):
    await _seed_products(pg_pool)
    async with session_factory() as session:  # type: ignore[call-arg]
        approved = await roi_repo.bulk_approve(session, ["A1", "A2"])
    assert sorted(approved) == ["A1", "A2"]
    async with session_factory() as verify_session:  # type: ignore[call-arg]
        result = await verify_session.execute(text("SELECT asin, status FROM products ORDER BY asin"))
        rows = result.fetchall()
    statuses = {row[0]: row[1] for row in rows}
    assert statuses == {"A1": "approved", "A2": "approved"}


@pytest.mark.asyncio
async def test_bulk_approve_rolls_back_on_error(monkeypatch, pg_pool, session_factory):
    await _seed_products(pg_pool)
    async with session_factory() as session:  # type: ignore[call-arg]
        original_execute = session.execute

        async def _failing_execute(self, stmt, params=None):
            if "UPDATE products" in str(stmt):
                await original_execute(stmt, params)
                raise RuntimeError("boom")
            return await original_execute(stmt, params)

        monkeypatch.setattr(session, "execute", types.MethodType(_failing_execute, session))
        with pytest.raises(RuntimeError):
            await roi_repo.bulk_approve(session, ["A1", "A2"])

    async with session_factory() as verify_session:  # type: ignore[call-arg]
        result = await verify_session.execute(text("SELECT asin, status FROM products ORDER BY asin"))
        rows = result.fetchall()
    statuses = {row[0]: row[1] for row in rows}
    assert statuses == {"A1": "pending", "A2": "pending"}
