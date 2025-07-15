from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import boto3
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timezone

from services.common.dsn import build_dsn

BUCKET = "awa-bucket"


def _log_load(conn, *, source: str, table: str, rows: int, status: str) -> None:
    conn.execute(
        text(
            "INSERT INTO load_log "
            "(source, target_table, inserted_rows, status, inserted_at) "
            "VALUES (:src, :tbl, :rows, :st, :ts)"
        ),
        {
            "src": source,
            "tbl": table,
            "rows": rows,
            "st": status,
            "ts": datetime.now(timezone.utc),
        },
    )


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


def main(argv: list[str] | None = None) -> int:
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

    inserted_rows = len(df)

    engine = create_engine(build_dsn(sync=True))
    try:
        with engine.begin() as conn:
            _log_load(
                conn,
                source=args.source,
                table=args.table,
                rows=inserted_rows,
                status="success",
            )
    except Exception:
        with engine.begin() as conn:
            _log_load(
                conn,
                source=args.source,
                table=args.table,
                rows=0,
                status="error",
            )
        raise
    return inserted_rows


if __name__ == "__main__":
    main()
