from __future__ import annotations

import argparse
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import boto3
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from services.common.dsn import build_dsn
from services.etl.dialects import amazon_reimbursements, amazon_returns, normalise_headers

BUCKET = "awa-bucket"


def _log_load(conn: Connection, *, source: str, table: str, rows: int, status: str) -> int:
    result = conn.execute(
        text(
            "INSERT INTO load_log "
            "(source, target_table, inserted_rows, status, inserted_at) "
            "VALUES (:src, :tbl, :rows, :st, :ts) RETURNING id"
        ),
        {"src": source, "tbl": table, "rows": rows, "st": status, "ts": datetime.now(timezone.utc)},
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


def main(argv: list[str] | None = None) -> tuple[int, int]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--table", default="auto")
    args = parser.parse_args(argv)

    if args.source.startswith("minio://"):
        file_path = _download_from_minio(args.source[len("minio://") :])
    else:
        file_path = Path(args.source)

    if file_path.suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)

    cols = normalise_headers(df.columns)
    dialect = None
    if amazon_returns.detect(cols):
        dialect = "returns_report"
        df = amazon_returns.normalise(df)
    elif amazon_reimbursements.detect(cols):
        dialect = "reimbursements_report"
        df = amazon_reimbursements.normalise(df)

    target_table = args.table
    if args.table == "auto" and dialect:
        target_table = {
            "returns_report": "returns_raw",
            "reimbursements_report": "reimbursements_raw",
        }[dialect]

    inserted_rows = len(df)

    engine = create_engine(build_dsn(sync=True))
    try:
        with engine.begin() as conn:
            if target_table != "auto":
                df.to_sql(target_table, conn, if_exists="append", index=False)
            load_id = _log_load(
                conn, source=args.source, table=target_table, rows=inserted_rows, status="success"
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
