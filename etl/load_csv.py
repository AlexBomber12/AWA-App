from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional, cast

import boto3
import pandas as pd
from sqlalchemy import create_engine

from services.common.dsn import build_dsn
from services.etl.dialects import (
    amazon_ads_sp_cost,
    amazon_fee_preview,
    amazon_inventory_ledger,
    amazon_reimbursements,
    amazon_returns,
    amazon_settlements,
    normalise_headers,
    schemas,
)
from services.ingest.copy_loader import copy_df_via_temp

USE_COPY = os.getenv("USE_COPY", "true").lower() in ("1", "true", "yes")
BUCKET = "awa-bucket"


def _read_csv_flex(path: Path) -> pd.DataFrame:
    for enc in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return pd.read_csv(path, sep=None, engine="python", encoding=enc)
        except UnicodeDecodeError:
            continue
        except Exception:
            pass
    for sep in (",", ";", "\t", "|"):
        try:
            return pd.read_csv(path, sep=sep)
        except Exception:
            continue
    raise RuntimeError(f"Failed to read CSV: {path}")


def _sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_from_minio(path: str) -> Path:
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
    *,
    force: bool = False,
) -> Dict[str, Any]:
    file_path = Path(path)
    file_hash = _sha256_file(file_path)

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
        elif amazon_fee_preview.detect(cols):
            dialect = "fee_preview_report"
            df = amazon_fee_preview.normalise(df)
        elif amazon_inventory_ledger.detect(cols):
            dialect = "inventory_ledger_report"
            df = amazon_inventory_ledger.normalise(df)
        elif amazon_ads_sp_cost.detect(cols):
            dialect = "ads_sp_cost_daily_report"
            df = amazon_ads_sp_cost.normalise(df)
        elif amazon_settlements.detect(cols):
            dialect = "settlements_txn_report"
            df = amazon_settlements.normalise(df)
        else:
            raise RuntimeError("Unknown report: cannot detect dialect")
    else:
        if dialect == "returns_report":
            df = amazon_returns.normalise(df)
        elif dialect == "reimbursements_report":
            df = amazon_reimbursements.normalise(df)
        elif dialect == "fee_preview_report":
            df = amazon_fee_preview.normalise(df)
        elif dialect == "inventory_ledger_report":
            df = amazon_inventory_ledger.normalise(df)
        elif dialect == "ads_sp_cost_daily_report":
            df = amazon_ads_sp_cost.normalise(df)
        elif dialect == "settlements_txn_report":
            df = amazon_settlements.normalise(df)
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
        "fee_preview_report": amazon_fee_preview.TARGET_TABLE,
        "inventory_ledger_report": amazon_inventory_ledger.TARGET_TABLE,
        "ads_sp_cost_daily_report": amazon_ads_sp_cost.TARGET_TABLE,
        "settlements_txn_report": amazon_settlements.TARGET_TABLE,
    }[dialect]

    idempotent = os.getenv("INGEST_IDEMPOTENT", "true").lower() in ("1", "true", "yes")
    analyze_min = int(os.getenv("ANALYZE_MIN_ROWS", "50000"))
    warnings: list[str] = []

    engine = create_engine(build_dsn(sync=True))
    conn = cast(Any, engine.raw_connection())
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            key = int(file_hash[:16], 16) % (2**63)
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (key,))
            if idempotent and not force:
                cur.execute(
                    "SELECT 1 FROM load_log WHERE target_table=%s AND file_hash=%s AND status='success' LIMIT 1",
                    (target_table, file_hash),
                )
                if cur.fetchone():
                    cur.execute(
                        "INSERT INTO load_log (source_uri, target_table, dialect, file_hash, status, finished_at) VALUES (%s,%s,%s,%s,'skipped',now())",
                        (str(file_path), target_table, dialect, file_hash),
                    )
                    conn.commit()
                    return {
                        "status": "skipped",
                        "rows": 0,
                        "dialect": dialect,
                        "target_table": target_table,
                        "warnings": warnings,
                    }

        columns = {
            "returns_report": list(df.columns),
            "reimbursements_report": list(df.columns),
            "fee_preview_report": amazon_fee_preview.TARGET_COLUMNS,
            "inventory_ledger_report": amazon_inventory_ledger.TARGET_COLUMNS,
            "ads_sp_cost_daily_report": amazon_ads_sp_cost.TARGET_COLUMNS,
            "settlements_txn_report": amazon_settlements.TARGET_COLUMNS,
        }[dialect]

        conflict_cols: tuple[str, ...] | None
        if dialect == "reimbursements_report":
            conflict_cols = ("reimb_id",)
        elif dialect == "ads_sp_cost_daily_report" and df["keyword_id"].notna().all():
            conflict_cols = amazon_ads_sp_cost.CONFLICT_COLS
        elif dialect == "settlements_txn_report" and df["transaction_id"].notna().all():
            conflict_cols = amazon_settlements.CONFLICT_COLS
        else:
            conflict_cols = None

        if USE_COPY:
            copy_df_via_temp(
                engine,
                df,
                target_table=target_table,
                target_schema=None,
                columns=columns,
                conflict_cols=conflict_cols,
                analyze_after=False,
                connection=conn,
            )
        else:
            df.to_sql(target_table, engine, if_exists="append", index=False)

        if len(df) >= analyze_min:
            with conn.cursor() as cur:
                cur.execute(f"ANALYZE {target_table}")

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO load_log (source_uri, target_table, dialect, file_hash, rows, status, warnings, finished_at) VALUES (%s,%s,%s,%s,%s,'success',%s,now())",
                (
                    str(file_path),
                    target_table,
                    dialect,
                    file_hash,
                    len(df),
                    json.dumps(warnings),
                ),
            )
        conn.commit()
        if celery_update:
            celery_update({"stage": "write", "rows": len(df)})
        return {
            "status": "success",
            "rows": len(df),
            "dialect": dialect,
            "target_table": target_table,
            "warnings": warnings,
        }
    except Exception as exc:  # pragma: no cover - defensive
        conn.rollback()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO load_log (source_uri, target_table, dialect, file_hash, status, error_summary, finished_at) VALUES (%s,%s,%s,%s,'error',%s,now())",
                (str(file_path), target_table, dialect, file_hash, str(exc)[:4000]),
            )
        conn.commit()
        raise
    finally:
        conn.close()
        engine.dispose()


def main(args: list[str]) -> tuple[int, int]:
    """Placeholder CLI entrypoint for type checking."""
    return 0, 0
