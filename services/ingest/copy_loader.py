from __future__ import annotations

import io
from typing import Optional, Sequence

import pandas as pd
from psycopg2 import sql
from sqlalchemy.engine import Engine


def _ensure_ident(name: str) -> sql.Identifier:
    """Return a safely quoted SQL identifier."""
    return sql.Identifier(name)


def _fq_ident(schema: Optional[str], table: str) -> sql.SQL:
    if schema:
        return sql.SQL(".").join([_ensure_ident(schema), _ensure_ident(table)])
    return _ensure_ident(table)


def copy_df_via_temp(
    engine: Engine,
    df: pd.DataFrame,
    target_table: str,
    *,
    target_schema: Optional[str] = None,
    columns: Sequence[str],
    conflict_cols: Optional[Sequence[str]] = None,
    analyze_after: bool = False,
) -> int:
    """Bulk load *df* into *target_table* using COPY and a staging table.

    The dataframe is first written to a TEMP table created ``LIKE`` the target
    including defaults and generated columns.  Data is streamed via ``COPY`` and
    then inserted into the final table.  If ``conflict_cols`` is provided an
    ``INSERT ... ON CONFLICT DO UPDATE`` is issued for the non-conflicting
    columns, otherwise rows are simply appended.

    Returns the number of rows provided in ``df``.
    """
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

    with engine.raw_connection() as conn:
        conn.autocommit = False
        try:
            with conn.cursor() as cur:
                if target_schema:
                    cur.execute(
                        sql.SQL("SET LOCAL search_path TO {}, public").format(
                            _ensure_ident(target_schema)
                        )
                    )

                cur.execute(
                    sql.SQL(
                        "CREATE TEMP TABLE {} (LIKE {} INCLUDING DEFAULTS INCLUDING GENERATED) ON COMMIT DROP"
                    ).format(stg, tgt)
                )

                copy_stmt = sql.SQL(
                    "COPY {} ({}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')"
                ).format(stg, cols_csv)
                cur.copy_expert(copy_stmt.as_string(conn), buf)

                if conflict_cols:
                    conflict_ident = [_ensure_ident(c) for c in conflict_cols]
                    conflict_list = sql.SQL(",").join(conflict_ident)
                    update_cols = [c for c in columns if c not in set(conflict_cols)]
                    if update_cols:
                        set_clause = sql.SQL(",").join(
                            [
                                sql.SQL("{} = EXCLUDED.{}").format(
                                    _ensure_ident(c), _ensure_ident(c)
                                )
                                for c in update_cols
                            ]
                        )
                        ins = sql.SQL(
                            "INSERT INTO {} ({}) SELECT {} FROM {} ON CONFLICT ({}) DO UPDATE SET {}"
                        ).format(
                            tgt, cols_csv, cols_csv, stg, conflict_list, set_clause
                        )
                    else:
                        ins = sql.SQL(
                            "INSERT INTO {} ({}) SELECT {} FROM {} ON CONFLICT ({}) DO NOTHING"
                        ).format(tgt, cols_csv, cols_csv, stg, conflict_list)
                    cur.execute(ins)
                else:
                    ins = sql.SQL("INSERT INTO {} ({}) SELECT {} FROM {}").format(
                        tgt, cols_csv, cols_csv, stg
                    )
                    cur.execute(ins)

                if analyze_after:
                    cur.execute(sql.SQL("ANALYZE {}").format(tgt))

            conn.commit()
            return len(df)
        except Exception:
            conn.rollback()
            raise
