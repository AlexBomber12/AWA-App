from __future__ import annotations

import argparse
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import boto3
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from services.common.dsn import build_dsn
from services.etl.dialects import (
    amazon_reimbursements,
    amazon_returns,
    normalise_headers,
    schemas,
)
from services.ingest.copy_loader import copy_df_via_temp

USE_COPY = os.getenv("USE_COPY", "true").lower() in ("1", "true", "yes")

BUCKET = "awa-bucket"


def _read_csv_flex(path: Path) -> pd.DataFrame:
    # try encodings with sniffer
    for enc in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return pd.read_csv(path, sep=None, engine="python", encoding=enc)
        except UnicodeDecodeError:
            continue
        except Exception:
            pass
    # fallback to explicit separators
    for sep in (",", ";", "\t", "|"):
        try:
            return pd.read_csv(path, sep=sep)
        except Exception:
            continue
    raise RuntimeError(f"Failed to read CSV: {path}")


def _log_load(
    conn: Connection, *, source: str, table: str, rows: int, status: str
) -> int:
    result = conn.execute(
        text(
            "INSERT INTO load_log "
            "(source, target_table, inserted_rows, status, inserted_at) "
            "VALUES (:src, :tbl, :rows, :st, :ts) RETURNING id"
        ),
        {
            "src": source,
            "tbl": table,
            "rows": rows,
            "st": status,
            "ts": datetime.now(timezone.utc),
        },
    )
    return int(result.scalar_one())


def _download_from_minio(path: str) -> Path:
    # path like raw/amazon/2024-06/file.csv
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    access = os.getenv("MINIO_ACCESS_KEY", "minio")
    secret = os.getenv("MINIO_SECRET_KEY", "minio123")
    s3 = boto3.client(
        "s3",
        endpoint_url=f"http://{endpoint}",
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name="us-east-1",
    )
    tmp = tempfile.NamedTemporaryFile(delete=False)
    s3.download_fileobj(BUCKET, path, tmp)
    tmp.close()
    return Path(tmp.name)


def import_file(
    path: str,
    report_type: Optional[str] = None,
    celery_update: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Import a CSV/Excel file into Postgres.

    Parameters
    ----------
    path:
        Path to local file.
    report_type:
        Optional explicit dialect name. If ``None`` the dialect is detected
        automatically.
    celery_update:
        Optional callback used by Celery tasks to report progress.
    """

    file_path = Path(path)
    if file_path.suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path)
    else:
        df = _read_csv_flex(file_path)
    if celery_update:
        celery_update({"stage": "read", "rows": len(df)})

    cols = normalise_headers(df.columns)
    dialect = report_type
    if dialect is None:
        if amazon_returns.detect(cols):
            dialect = "returns_report"
            df = amazon_returns.normalise(df)
        elif amazon_reimbursements.detect(cols):
            dialect = "reimbursements_report"
            df = amazon_reimbursements.normalise(df)
        else:
            raise RuntimeError("Unknown report: cannot detect dialect")
    if celery_update:
        celery_update({"stage": "detect", "dialect": dialect})

    df = schemas.validate(df, dialect)
    if celery_update:
        celery_update({"stage": "validate", "rows": len(df)})

    target_table = {
        "returns_report": "returns_raw",
        "reimbursements_report": "reimbursements_raw",
    }[dialect]

    engine = create_engine(build_dsn(sync=True))
    try:
        if USE_COPY:
            conflict_cols = (
                ("reimb_id",) if dialect == "reimbursements_report" else None
            )
            copy_df_via_temp(
                engine,
                df,
                target_table=target_table,
                target_schema=None,
                columns=list(df.columns),
                conflict_cols=conflict_cols,
                analyze_after=False,
            )
        else:
            with engine.begin() as conn:
                df.to_sql(target_table, conn, if_exists="append", index=False)
    finally:
        engine.dispose()
    if celery_update:
        celery_update({"stage": "write", "rows": len(df)})

    return {
        "rows": len(df),
        "dialect": dialect,
        "target_table": target_table,
        "warnings": [],
    }


def main(argv: list[str] | None = None) -> tuple[int, int]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--table", default="auto")
    args = parser.parse_args(argv)

    if args.source.startswith("minio://"):
        file_path = _download_from_minio(args.source[len("minio://") :])
    else:
        file_path = Path(args.source)

    summary = import_file(str(file_path), report_type=None)

    target_table = args.table
    if args.table == "auto" and summary.get("dialect"):
        target_table = {
            "returns_report": "returns_raw",
            "reimbursements_report": "reimbursements_raw",
        }[summary["dialect"]]

    inserted_rows = summary.get("rows", 0)

    engine = create_engine(build_dsn(sync=True))
    try:
        with engine.begin() as conn:
            load_id = _log_load(
                conn,
                source=args.source,
                table=target_table,
                rows=inserted_rows,
                status="success",
            )
    except Exception:
        with engine.begin() as conn:
            load_id = _log_load(
                conn, source=args.source, table=target_table, rows=0, status="error"
            )
        raise
    return load_id, inserted_rows


if __name__ == "__main__":
    main()
