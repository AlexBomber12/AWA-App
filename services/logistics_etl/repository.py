from __future__ import annotations

import time
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from typing import Any

from sqlalchemy import Column, MetaData, Table, func, literal_column, or_, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.sql.sqltypes import NullType

from awa_common.dsn import build_dsn
from awa_common.metrics import record_logistics_upsert_batch, record_logistics_upsert_rows
from awa_common.settings import Settings

_engine: AsyncEngine | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(build_dsn(sync=False), future=True)
    return _engine


def _prepare_row(row: Mapping[str, Any]) -> dict[str, Any]:
    prepared = dict(row)
    for key in ("effective_from", "effective_to"):
        value = prepared.get(key)
        if value in (None, "", "null"):
            prepared[key] = None
            continue
        if isinstance(value, date):
            prepared[key] = value
            continue
        if isinstance(value, datetime):
            prepared[key] = value.date()
            continue
        if isinstance(value, str):
            prepared[key] = date.fromisoformat(value)
            continue
        raise ValueError(f"Unsupported date value for {key}: {value!r}")
    return prepared


async def upsert_many(  # noqa: C901
    *,
    table: str,
    key_cols: Sequence[str],
    rows: Iterable[Mapping[str, Any]],
    update_columns: Sequence[str] | None = None,
) -> dict[str, int]:
    cfg = Settings()
    incoming = [_prepare_row(row) for row in rows]
    if not incoming:
        return {"inserted": 0, "updated": 0, "skipped": 0}

    update_columns = list(update_columns or [])
    if not key_cols:
        raise ValueError("at least one key column is required")

    engine = _get_engine()
    inserted = updated = 0
    batch_size = max(1, int(cfg.LOGISTICS_UPSERT_BATCH_SIZE))
    statement_timeout_ms = max(0, int(cfg.DB_STATEMENT_TIMEOUT_SECONDS) * 1000)
    all_columns = sorted({col for row in incoming for col in row.keys()})
    metadata = MetaData()
    table_obj = Table(
        table,
        metadata,
        *[Column(col, NullType()) for col in all_columns],
    )

    async def _execute_batch(batch: list[dict[str, Any]]) -> tuple[int, int]:
        stmt = pg_insert(table_obj).values(batch)
        excluded = stmt.excluded
        set_clauses: dict[str, Any] = {}
        distinct_checks = []
        for col in update_columns:
            if col == "updated_at":
                set_clauses[col] = func.now()
                continue
            set_clauses[col] = excluded[col]
            distinct_checks.append(getattr(table_obj.c, col).is_distinct_from(excluded[col]))
        if "updated_at" not in set_clauses:
            set_clauses["updated_at"] = func.now()

        conflict_cols = [getattr(table_obj.c, col) for col in key_cols]
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_=set_clauses,
            where=or_(*distinct_checks) if distinct_checks else None,
        ).returning(literal_column("xmax = 0").label("inserted_flag"))

        async with engine.begin() as conn:
            if cfg.TESTING and statement_timeout_ms:
                await conn.execute(text("SET LOCAL statement_timeout = :ms"), {"ms": statement_timeout_ms})
            result = await conn.execute(stmt)
            rows = result.fetchall()
        inserted_batch = sum(1 for row in rows if bool(row.inserted_flag))
        updated_batch = len(rows) - inserted_batch
        return inserted_batch, updated_batch

    for offset in range(0, len(incoming), batch_size):
        batch = incoming[offset : offset + batch_size]
        start = time.perf_counter()
        batch_inserted, batch_updated = await _execute_batch(batch)
        duration = time.perf_counter() - start
        inserted += batch_inserted
        updated += batch_updated
        skipped_batch = max(0, len(batch) - (batch_inserted + batch_updated))
        record_logistics_upsert_rows("inserted", batch_inserted)
        record_logistics_upsert_rows("updated", batch_updated)
        record_logistics_upsert_rows("skipped", skipped_batch)
        record_logistics_upsert_batch(duration)

    skipped = max(0, len(incoming) - (inserted + updated))
    return {"inserted": inserted, "updated": updated, "skipped": skipped}


async def seen_load(source: str, sha256: str | None, seqno: str | None) -> bool:
    if not source:
        return False
    if sha256 is None and seqno is None:
        return False

    engine = _get_engine()
    query = text(
        """
        SELECT 1
          FROM logistics_loadlog
         WHERE source = :source
           AND (
                (:sha256 IS NOT NULL AND sha256 = :sha256)
             OR (:seqno IS NOT NULL AND seqno = :seqno)
           )
         LIMIT 1
        """
    )
    params = {"source": source, "sha256": sha256, "seqno": seqno}
    async with engine.connect() as conn:
        result = await conn.execute(query, params)
        return result.scalar_one_or_none() is not None


async def mark_load(source: str, sha256: str | None, seqno: str | None, rows: int) -> None:
    engine = _get_engine()
    query = text(
        """
        INSERT INTO logistics_loadlog (source, sha256, seqno, rows)
        VALUES (:source, :sha256, :seqno, :rows)
        ON CONFLICT DO NOTHING
        """
    )
    async with engine.begin() as conn:
        await conn.execute(query, {"source": source, "sha256": sha256, "seqno": seqno, "rows": rows})


if Settings().TESTING:

    def _upsert_many_with_keys(
        engine: Engine,
        *,
        table: str,
        key_cols: Sequence[str],
        rows: Iterable[Mapping[str, Any]],
        update_columns: Sequence[str] | None = None,
        testing: bool = False,
    ) -> dict[str, int] | None:
        """
        TESTING-only helper: generic UPSERT into `table` with explicit `key_cols`.
        Updates only columns listed in `update_columns` (if provided), using IS DISTINCT FROM
        to avoid churn. Returns summary {'inserted','updated','skipped'} when testing=True.
        """
        incoming = list(rows)
        if not incoming:
            return {"inserted": 0, "updated": 0, "skipped": 0} if testing else None

        # Determine columns
        all_cols = list({k for r in incoming for k in r.keys()})
        keys = list(key_cols)
        if update_columns is None:
            update_columns = [c for c in all_cols if c not in keys]
        upd = list(update_columns)

        # Build VALUES table and params
        cols = keys + upd
        values_rows = []
        params: dict[str, Any] = {}
        for i, r in enumerate(incoming):
            values_rows.append(f"({', '.join(f':{c}{i}' for c in cols)})")
            for c in cols:
                params[f"{c}{i}"] = r.get(c)
        values_sql = ", ".join(values_rows)

        insert_sql = f"""
        INSERT INTO {table} ({", ".join(cols)})
        VALUES {values_sql}
        ON CONFLICT ({", ".join(keys)}) DO NOTHING;
        """

        set_assign = ", ".join([f"{c} = v.{c}" for c in upd])
        is_changed = " OR ".join([f"t.{c} IS DISTINCT FROM v.{c}" for c in upd]) or "FALSE"
        values_cols = ", ".join(cols)
        update_sql = f"""
        WITH v({values_cols}) AS (VALUES {values_sql})
        UPDATE {table} AS t
        SET {set_assign}
        FROM v
        WHERE {" AND ".join([f"t.{k} = v.{k}" for k in keys])}
          AND ({is_changed});
        """

        inserted = updated = 0
        with engine.begin() as conn:
            r1 = conn.execute(text(insert_sql), params)
            inserted = getattr(r1, "rowcount", 0) or 0
            r2 = conn.execute(text(update_sql), params)
            updated = getattr(r2, "rowcount", 0) or 0
        if testing:
            skipped = max(0, len(incoming) - (inserted + updated))
            return {"inserted": inserted, "updated": updated, "skipped": skipped}
        return None
