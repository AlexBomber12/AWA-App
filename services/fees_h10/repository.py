import os
from typing import Any, Dict, Iterable, Mapping

from sqlalchemy import text
from sqlalchemy.engine import Engine


def _fees_table() -> str:
    return os.getenv("FEES_RAW_TABLE", "fees_raw")


def upsert_fees_raw(
    engine: Engine, rows: Iterable[Mapping[str, Any]], *, testing: bool = False
) -> dict[str, int] | None:
    """Idempotent upsert for fees.

    TESTING-only: returns counts for inserted/updated/skipped rows.
    Assumes logical key (asin, marketplace, fee_type).
    Only updates when one of the mutable fields changes.
    """

    rows = list(rows)
    if not rows:
        return {"inserted": 0, "updated": 0, "skipped": 0} if testing else None

    tbl = _fees_table()
    keys = ("asin", "marketplace", "fee_type")
    mutable = ("amount", "currency", "source", "effective_date")

    cols = keys + mutable

    def _param(c: str, i: int) -> str:
        if c == "effective_date":
            # SQLAlchemy's text parser does not recognize the ``:param::TYPE``
            # syntax when compiling for psycopg, leaving ``:param::DATE`` in the
            # rendered SQL and causing a syntax error. Use an explicit CAST so
            # the parameter can be bound normally.
            return f"CAST(:{c}{i} AS DATE)"
        return f":{c}{i}"

    values_sql = ", ".join(
        [f"({', '.join([_param(c, i) for c in cols])})" for i in range(len(rows))]
    )
    params: Dict[str, Any] = {}
    for i, r in enumerate(rows):
        for c in cols:
            params[f"{c}{i}"] = r.get(c)

    insert_sql = f"""
    INSERT INTO {tbl} ({", ".join(cols)})
    VALUES {values_sql}
    ON CONFLICT ({", ".join(keys)}) DO NOTHING;
    """

    values_cols = ", ".join([f"{c}" for c in cols])
    values_pairs = ", ".join(
        [f"({', '.join([_param(c, i) for c in cols])})" for i in range(len(rows))]
    )
    set_assign = ", ".join([f"{m} = v.{m}" for m in mutable])
    is_changed = " OR ".join([f"t.{m} IS DISTINCT FROM v.{m}" for m in mutable])

    update_sql = f"""
    WITH v({values_cols}) AS (VALUES {values_pairs})
    UPDATE {tbl} AS t
    SET {set_assign}
    FROM v
    WHERE t.asin = v.asin AND t.marketplace = v.marketplace AND t.fee_type = v.fee_type
      AND ({is_changed});
    """

    inserted = updated = 0
    with engine.begin() as conn:
        res1 = conn.execute(text(insert_sql), params)
        inserted = getattr(res1, "rowcount", 0) or 0
        res2 = conn.execute(text(update_sql), params)
        updated = getattr(res2, "rowcount", 0) or 0

    if testing:
        skipped = max(0, len(rows) - (inserted + updated))
        return {"inserted": inserted, "updated": updated, "skipped": skipped}
    return None
