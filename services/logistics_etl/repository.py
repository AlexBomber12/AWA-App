from __future__ import annotations

import os
from typing import Any, Dict, Iterable, Mapping, Sequence

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


async def upsert_many(rows: Iterable[dict]) -> None:
    query = text(
        """
        INSERT INTO freight_rates (lane, mode, eur_per_kg)
        VALUES (:lane, :mode, :eur_per_kg)
        ON CONFLICT (lane, mode) DO UPDATE SET
          eur_per_kg = EXCLUDED.eur_per_kg,
          updated_at = CURRENT_TIMESTAMP
        """
    )
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.execute(query, list(rows))


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
        params: Dict[str, Any] = {}
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
        is_changed = (
            " OR ".join([f"t.{c} IS DISTINCT FROM v.{c}" for c in upd]) or "FALSE"
        )
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
