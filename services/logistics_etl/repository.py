from __future__ import annotations

import os
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from .dsn import build_dsn

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
    incoming = [_prepare_row(row) for row in rows]
    if not incoming:
        return {"inserted": 0, "updated": 0, "skipped": 0}

    update_columns = list(update_columns or [])
    engine = _get_engine()
    inserted = updated = 0

    async with engine.begin() as conn:
        for row in incoming:
            params = dict(row)
            where_clauses: list[str] = []
            for key in key_cols:
                if key == "effective_from":
                    where_clauses.append(
                        "COALESCE(effective_from, DATE '1900-01-01') = COALESCE(:effective_from, DATE '1900-01-01')"
                    )
                else:
                    where_clauses.append(f"{key} = :{key}")
            if not where_clauses:
                raise ValueError("at least one key column is required")

            set_parts: list[str] = []
            change_checks: list[str] = []
            for col in update_columns:
                if col == "updated_at":
                    set_parts.append("updated_at = CURRENT_TIMESTAMP")
                else:
                    set_parts.append(f"{col} = :{col}")
                    change_checks.append(f"{col} IS DISTINCT FROM :{col}")
            if not set_parts:
                set_parts.append("updated_at = CURRENT_TIMESTAMP")

            update_sql = f"""
                UPDATE {table}
                   SET {", ".join(set_parts)}
                 WHERE {" AND ".join(where_clauses)}
            """
            if change_checks:
                update_sql += f" AND ({' OR '.join(change_checks)})"
            update_sql += " RETURNING 1"

            result = await conn.execute(text(update_sql), params)
            if result.scalar_one_or_none():
                updated += 1
                continue

            insert_cols = list(row.keys())
            placeholders = ", ".join(f":{col}" for col in insert_cols)
            insert_sql = f"""
                INSERT INTO {table} ({", ".join(insert_cols)})
                VALUES ({placeholders})
            """
            await conn.execute(text(insert_sql), params)
            inserted += 1

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


if os.getenv("TESTING") == "1":

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
