from __future__ import annotations

import io
from collections.abc import Sequence
from typing import Any, cast

import pandas as pd
from psycopg2 import sql
from sqlalchemy.engine import Engine


def _ensure_ident(name: str) -> sql.Identifier:
    """Return a safely quoted SQL identifier."""
    return sql.Identifier(name)


def _fq_ident(schema: str | None, table: str) -> sql.SQL:
    if schema:
        return sql.SQL(".").join([_ensure_ident(schema), _ensure_ident(table)])
    return _ensure_ident(table)


def copy_df_via_temp(  # noqa: C901
    engine: Engine,
    df: pd.DataFrame,
    target_table: str,
    *,
    target_schema: str | None = None,
    columns: Sequence[str],
    conflict_cols: Sequence[str] | None = None,
    analyze_after: bool = False,
    connection: Any | None = None,
) -> int:
    """Bulk load *df* into *target_table* using COPY and a staging table."""
    if not len(df):
        return 0

    ordered_df = df.loc[:, list(columns)]
    buf = io.StringIO()
    ordered_df.to_csv(buf, index=False, na_rep="")
    buf.seek(0)

    tgt = _fq_ident(target_schema, target_table)
    cols_ident = [_ensure_ident(c) for c in columns]
    cols_csv = sql.SQL(",").join(cols_ident)

    temp_name = f"stg_{target_table}_tmp"
    stg = _ensure_ident(temp_name)

    manage_conn = connection is None
    conn = cast(Any, connection or engine.raw_connection())
    if manage_conn:
        conn.autocommit = False
    try:
        with conn.cursor() as cur:
            if target_schema:
                cur.execute(sql.SQL("SET LOCAL search_path TO {}, public").format(_ensure_ident(target_schema)))

            cur.execute(
                sql.SQL("CREATE TEMP TABLE {} (LIKE {} INCLUDING DEFAULTS INCLUDING GENERATED) ON COMMIT DROP").format(
                    stg, tgt
                )
            )

            copy_stmt = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')").format(stg, cols_csv)
            cur.copy_expert(copy_stmt.as_string(conn), buf)

            if conflict_cols:
                conflict_ident = [_ensure_ident(c) for c in conflict_cols]
                conflict_list = sql.SQL(",").join(conflict_ident)
                update_cols = [c for c in columns if c not in set(conflict_cols)]
                if update_cols:
                    set_clause = sql.SQL(",").join(
                        [sql.SQL("{} = EXCLUDED.{}").format(_ensure_ident(c), _ensure_ident(c)) for c in update_cols]
                    )
                    ins = sql.SQL("INSERT INTO {} ({}) SELECT {} FROM {} ON CONFLICT ({}) DO UPDATE SET {}").format(
                        tgt, cols_csv, cols_csv, stg, conflict_list, set_clause
                    )
                else:
                    ins = sql.SQL("INSERT INTO {} ({}) SELECT {} FROM {} ON CONFLICT ({}) DO NOTHING").format(
                        tgt, cols_csv, cols_csv, stg, conflict_list
                    )
                cur.execute(ins)
            else:
                ins = sql.SQL("INSERT INTO {} ({}) SELECT {} FROM {}").format(tgt, cols_csv, cols_csv, stg)
                cur.execute(ins)

            if analyze_after:
                cur.execute(sql.SQL("ANALYZE {}").format(tgt))

        if manage_conn:
            conn.commit()
        return len(df)
    except Exception:
        if manage_conn:
            conn.rollback()
        raise
    finally:
        if manage_conn:
            conn.close()
