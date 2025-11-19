from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import boto3
import pandas as pd
from sqlalchemy import create_engine, text

from awa_common.dsn import build_dsn
from awa_common.settings import settings
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
from services.worker.copy_loader import copy_df_via_temp


class ImportFileError(RuntimeError):
    """Raised when the ETL pipeline fails after persisting load_log metadata."""

    status_code = 500

    def to_meta(self) -> dict[str, str]:
        return {"status": "error", "error": str(self)}


class ImportValidationError(ImportFileError):
    """Raised for user-facing issues (e.g. empty or malformed uploads)."""

    status_code = 422


_ETL_CFG = getattr(settings, "etl", None)
_S3_CFG = getattr(settings, "s3", None)
USE_COPY = bool(_ETL_CFG.use_copy if _ETL_CFG else getattr(settings, "USE_COPY", True))
STREAMING_CHUNK_ENV = int(
    _ETL_CFG.ingest_streaming_chunk_size if _ETL_CFG else getattr(settings, "INGEST_STREAMING_CHUNK_SIZE", 50_000)
)
BUCKET = _S3_CFG.bucket if _S3_CFG else getattr(settings, "MINIO_BUCKET", "awa-bucket")
CSV_EXTENSIONS = {".csv", ".txt", ".tsv"}
XLSX_EXTENSIONS = {".xlsx", ".xlsm"}


@dataclass(slots=True)
class _StreamingMetadata:
    dialect: str
    rows: int
    keyword_full: bool
    transaction_full: bool


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
    raise ImportValidationError(f"Failed to read CSV: {path}")


def _sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_from_minio(path: str) -> Path:
    s3_cfg = getattr(settings, "s3", None)
    endpoint = s3_cfg.endpoint if s3_cfg else getattr(settings, "MINIO_ENDPOINT", "minio:9000")
    secure = bool(s3_cfg.secure if s3_cfg else getattr(settings, "MINIO_SECURE", False))
    access = s3_cfg.access_key if s3_cfg else getattr(settings, "MINIO_ACCESS_KEY", "minio")
    secret = s3_cfg.secret_key if s3_cfg else getattr(settings, "MINIO_SECRET_KEY", "minio123")
    region = s3_cfg.region if s3_cfg else getattr(settings, "AWS_REGION", "us-east-1")
    scheme = "https" if secure else "http"
    endpoint_url = endpoint if "://" in endpoint else f"{scheme}://{endpoint}"
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name=region,
    )
    tmp = tempfile.NamedTemporaryFile(delete=False)
    s3.download_fileobj(BUCKET, path, tmp)
    tmp.close()
    return Path(tmp.name)


def _is_s3_uri(uri: str) -> bool:
    return isinstance(uri, str) and uri.startswith(("s3://", "minio://"))


def _open_uri(uri: str) -> Path:
    """
    TESTING-only hook: in tests we monkeypatch this to return a local file.
    In production, your existing S3/MinIO downloader remains in place.
    """
    if getattr(settings, "TESTING", False):
        return Path(uri)
    raise RuntimeError("S3/MinIO open is not available outside tests")


def _normalize_for_dialect(df: pd.DataFrame, dialect: str) -> pd.DataFrame:
    if dialect == "returns_report":
        return amazon_returns.normalise(df)
    if dialect == "reimbursements_report":
        return amazon_reimbursements.normalise(df)
    if dialect == "fee_preview_report":
        return amazon_fee_preview.normalise(df)
    if dialect == "inventory_ledger_report":
        return amazon_inventory_ledger.normalise(df)
    if dialect == "ads_sp_cost_daily_report":
        return amazon_ads_sp_cost.normalise(df)
    if dialect == "settlements_txn_report":
        return amazon_settlements.normalise(df)
    raise ImportValidationError("Unknown report: cannot detect dialect")


def _detect_dialect_from_columns(normalized_columns: list[str]) -> str:
    if amazon_returns.detect(normalized_columns):
        return "returns_report"
    if amazon_reimbursements.detect(normalized_columns):
        return "reimbursements_report"
    if amazon_fee_preview.detect(normalized_columns):
        return "fee_preview_report"
    if amazon_inventory_ledger.detect(normalized_columns):
        return "inventory_ledger_report"
    if amazon_ads_sp_cost.detect(normalized_columns):
        return "ads_sp_cost_daily_report"
    if amazon_settlements.detect(normalized_columns):
        return "settlements_txn_report"
    raise ImportValidationError("Unknown report: cannot detect dialect")


def _resolve_dialect(df: pd.DataFrame, explicit: str | None) -> tuple[str, pd.DataFrame]:
    if explicit:
        return explicit, _normalize_for_dialect(df, explicit)
    cols = normalise_headers(df.columns)
    detected = _detect_dialect_from_columns(cols)
    return detected, _normalize_for_dialect(df, detected)


def _conflict_columns_for(
    dialect: str,
    *,
    df: pd.DataFrame | None = None,
    metadata: _StreamingMetadata | None = None,
) -> tuple[str, ...] | None:
    if dialect == "reimbursements_report":
        return ("reimb_id",)
    if dialect == "ads_sp_cost_daily_report":
        keyword_safe = metadata.keyword_full if metadata else bool(df is not None and df["keyword_id"].notna().all())
        if keyword_safe:
            return amazon_ads_sp_cost.CONFLICT_COLS
        return None
    if dialect == "settlements_txn_report":
        txn_safe = (
            metadata.transaction_full if metadata else bool(df is not None and df["transaction_id"].notna().all())
        )
        if txn_safe:
            return amazon_settlements.CONFLICT_COLS
        return None
    return None


def _gather_streaming_metadata(path: Path, chunk_size: int, dialect_hint: str | None) -> _StreamingMetadata:
    dialect: str | None = None
    rows = 0
    keyword_full = True
    transaction_full = True
    for chunk in load_large_csv(path, chunk_size=chunk_size):
        if chunk is None or chunk.empty:
            continue
        if dialect is None:
            dialect, normalized = _resolve_dialect(chunk, dialect_hint)
        else:
            normalized = _normalize_for_dialect(chunk, dialect)
        if normalized.empty:
            continue
        rows += len(normalized)
        if "keyword_id" in normalized.columns and normalized["keyword_id"].isna().any():
            keyword_full = False
        if "transaction_id" in normalized.columns and normalized["transaction_id"].isna().any():
            transaction_full = False
    if dialect is None or rows == 0:
        raise ImportValidationError("empty file")
    return _StreamingMetadata(
        dialect=dialect,
        rows=rows,
        keyword_full=keyword_full,
        transaction_full=transaction_full,
    )


def _process_streaming_chunks(
    path: Path,
    *,
    chunk_size: int,
    dialect: str,
    engine: Any,
    conn: Any,
    target_table: str,
    columns: list[str] | None,
    conflict_cols: tuple[str, ...] | None,
) -> int:
    total = 0
    resolved_columns = list(columns) if columns else None
    for chunk in load_large_csv(path, chunk_size=chunk_size):
        if chunk is None or chunk.empty:
            continue
        normalized = _normalize_for_dialect(chunk, dialect)
        if normalized.empty:
            continue
        try:
            validated = schemas.validate(normalized, dialect)
        except ValueError as err:
            raise ImportValidationError(str(err)) from err
        if not len(validated):
            continue
        if USE_COPY:
            if resolved_columns is None:
                resolved_columns = list(validated.columns)
            copy_df_via_temp(
                engine,
                validated,
                target_table=target_table,
                target_schema=None,
                columns=resolved_columns,
                conflict_cols=conflict_cols,
                analyze_after=False,
                connection=conn,
            )
        else:
            validated.to_sql(target_table, engine, if_exists="append", index=False)
        total += len(validated)
    if total == 0:
        raise ImportValidationError("empty file")
    return total


def load_large_csv(path: Path, *, chunk_size: int = STREAMING_CHUNK_ENV) -> Iterator[pd.DataFrame]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    suffix = path.suffix.lower()
    if suffix in XLSX_EXTENSIONS:
        yield from _stream_xlsx_chunks(path, chunk_size)
        return
    if suffix in CSV_EXTENSIONS:
        yield from _stream_csv_chunks(path, chunk_size)
        return
    raise ImportValidationError(f"Streaming is only supported for CSV or XLSX files: {path}")


def _stream_csv_chunks(path: Path, chunk_size: int) -> Iterator[pd.DataFrame]:
    last_error: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            reader = pd.read_csv(path, sep=None, engine="python", encoding=encoding, chunksize=chunk_size)
        except UnicodeDecodeError as err:
            last_error = err
            continue
        except Exception as err:
            last_error = err
            continue
        yield from _yield_reader(reader)
        return
    for sep in (",", ";", "\t", "|"):
        try:
            reader = pd.read_csv(path, sep=sep, chunksize=chunk_size)
        except Exception as err:
            last_error = err
            continue
        yield from _yield_reader(reader)
        return
    raise ImportValidationError(f"Failed to read CSV: {path}") from last_error


def _stream_xlsx_chunks(path: Path, chunk_size: int) -> Iterator[pd.DataFrame]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ImportValidationError("openpyxl is required for XLSX streaming") from exc
    wb = load_workbook(filename=path, read_only=True, data_only=True)
    try:
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            headers: list[str] | None = None
            buffer: list[list[Any]] = []
            for row in ws.iter_rows(values_only=True):
                if headers is None:
                    if not row:
                        continue
                    header_values = [(cell if cell is not None else "") for cell in row]
                    if not any(header_values):
                        continue
                    headers = [str(cell).strip() for cell in header_values]
                    continue
                if row is None or not any(value is not None for value in row):
                    continue
                normalized_row = list(row[: len(headers)])
                if len(normalized_row) < len(headers):
                    normalized_row.extend([None] * (len(headers) - len(normalized_row)))
                buffer.append(normalized_row)
                if len(buffer) >= chunk_size:
                    yield pd.DataFrame(buffer, columns=headers)
                    buffer.clear()
            if headers and buffer:
                yield pd.DataFrame(buffer, columns=headers)
    finally:
        wb.close()


def _yield_reader(reader: pd.io.parsers.TextFileReader) -> Iterator[pd.DataFrame]:
    try:
        yield from reader
    finally:
        reader.close()


def import_file(  # noqa: C901
    path: str,
    report_type: str | None = None,
    celery_update: Callable[[dict[str, Any]], None] | None = None,
    *,
    force: bool = False,
    streaming: bool = False,
    chunk_size: int | None = None,
    idempotency_key: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    _dialect_override = kwargs.pop("dialect", None)
    if kwargs:
        raise TypeError(f"Unexpected kwargs: {', '.join(kwargs)}")
    TESTING = bool(getattr(settings, "TESTING", False))
    file_path = Path(path)
    if file_path.exists() and file_path.stat().st_size == 0:
        raise ImportValidationError("empty file")
    file_hash = idempotency_key or _sha256_file(file_path)
    if _dialect_override == "test_generic":
        streaming = False

    explicit_dialect = _dialect_override or report_type
    chunk_rows = chunk_size or STREAMING_CHUNK_ENV

    df: pd.DataFrame | None = None
    metadata: _StreamingMetadata | None = None
    dialect: str | None = None

    if streaming:
        if file_path.suffix.lower() == ".xls":
            raise ImportValidationError("Streaming requires XLSX files for Excel sources")
        metadata = _gather_streaming_metadata(file_path, chunk_rows, explicit_dialect)
        dialect = metadata.dialect
        if celery_update:
            celery_update({"stage": "read", "rows": metadata.rows})
            celery_update({"stage": "detect", "dialect": dialect})
    else:
        if file_path.suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(file_path)
        else:
            df = _read_csv_flex(file_path)
        if df is None or (hasattr(df, "empty") and df.empty):
            raise ImportValidationError("empty file")
        if celery_update:
            celery_update({"stage": "read", "rows": len(df)})

        if TESTING and _dialect_override == "test_generic":
            from services.etl.dialects import test_generic as td

            try:
                df = td.normalize_df(df)
            except ValueError as err:
                raise ImportValidationError(str(err)) from err
            engine = create_engine(build_dsn(sync=True))
            with engine.begin() as db_conn:
                for row in df.to_dict(orient="records"):
                    db_conn.execute(
                        text(
                            'INSERT INTO test_generic_raw("ASIN", qty, price) VALUES (:ASIN,:qty,:price) '
                            'ON CONFLICT ("ASIN") DO UPDATE SET qty=EXCLUDED.qty, price=EXCLUDED.price'
                        ),
                        row,
                    )
            return {
                "status": "success",
                "rows": len(df),
                "dialect": td.NAME,
                "target_table": td.TABLE,
                "warnings": [],
            }

        dialect, df = _resolve_dialect(df, explicit_dialect)
        if celery_update:
            celery_update({"stage": "detect", "dialect": dialect})

        try:
            df = schemas.validate(df, dialect)
        except ValueError as err:
            raise ImportValidationError(str(err)) from err
        if celery_update:
            celery_update({"stage": "validate", "rows": len(df)})

    if dialect is None:
        raise ImportValidationError("Unknown report: cannot detect dialect")

    target_table = {
        "returns_report": "returns_raw",
        "reimbursements_report": "reimbursements_raw",
        "fee_preview_report": amazon_fee_preview.TARGET_TABLE,
        "inventory_ledger_report": amazon_inventory_ledger.TARGET_TABLE,
        "ads_sp_cost_daily_report": amazon_ads_sp_cost.TARGET_TABLE,
        "settlements_txn_report": amazon_settlements.TARGET_TABLE,
    }[dialect]

    idempotent = bool(_ETL_CFG.ingest_idempotent if _ETL_CFG else getattr(settings, "INGEST_IDEMPOTENT", True))
    analyze_min = int(_ETL_CFG.analyze_min_rows if _ETL_CFG else getattr(settings, "ANALYZE_MIN_ROWS", 50_000))
    warnings: list[str] = []

    engine = create_engine(build_dsn(sync=True))
    conn: Any = engine.raw_connection()
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
                        (
                            "INSERT INTO load_log (source_uri, target_table, dialect, file_hash, "
                            "status, finished_at) VALUES "
                            "(%s,%s,%s,%s,'skipped',now())"
                        ),
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

        column_map: dict[str, list[str] | None] = {
            "returns_report": list(df.columns) if df is not None else None,
            "reimbursements_report": list(df.columns) if df is not None else None,
            "fee_preview_report": list(amazon_fee_preview.TARGET_COLUMNS),
            "inventory_ledger_report": list(amazon_inventory_ledger.TARGET_COLUMNS),
            "ads_sp_cost_daily_report": list(amazon_ads_sp_cost.TARGET_COLUMNS),
            "settlements_txn_report": list(amazon_settlements.TARGET_COLUMNS),
        }
        columns = column_map[dialect]
        conflict_cols = _conflict_columns_for(dialect, df=df, metadata=metadata)

        if streaming:
            rows_loaded = _process_streaming_chunks(
                file_path,
                chunk_size=chunk_rows,
                dialect=dialect,
                engine=engine,
                conn=conn,
                target_table=target_table,
                columns=columns,
                conflict_cols=conflict_cols,
            )
        else:
            assert df is not None
            if USE_COPY:
                assert columns is not None
                copy_df_via_temp(
                    engine,
                    df,
                    target_table=target_table,
                    target_schema=None,
                    columns=list(columns),
                    conflict_cols=conflict_cols,
                    analyze_after=False,
                    connection=conn,
                )
            else:
                df.to_sql(target_table, engine, if_exists="append", index=False)
            rows_loaded = len(df)

        if rows_loaded >= analyze_min:
            with conn.cursor() as cur:
                cur.execute(f"ANALYZE {target_table}")

        with conn.cursor() as cur:
            cur.execute(
                (
                    "INSERT INTO load_log (source_uri, target_table, dialect, file_hash, rows, status, "
                    "warnings, finished_at) VALUES (%s,%s,%s,%s,%s,'success',%s,now())"
                ),
                (
                    str(file_path),
                    target_table,
                    dialect,
                    file_hash,
                    rows_loaded,
                    json.dumps(warnings),
                ),
            )
        conn.commit()
        if celery_update:
            if streaming:
                celery_update({"stage": "validate", "rows": rows_loaded})
            celery_update({"stage": "write", "rows": rows_loaded})
        return {
            "status": "success",
            "rows": rows_loaded,
            "dialect": dialect,
            "target_table": target_table,
            "warnings": warnings,
        }
    except ImportFileError:
        conn.rollback()
        raise
    except Exception as exc:  # pragma: no cover - defensive
        conn.rollback()
        with conn.cursor() as cur:
            cur.execute(
                (
                    "INSERT INTO load_log (source_uri, target_table, dialect, file_hash, status, "
                    "error_summary, finished_at) VALUES (%s,%s,%s,%s,'error',%s,now())"
                ),
                (str(file_path), target_table, dialect, file_hash, str(exc)[:4000]),
            )
        conn.commit()
        raise ImportFileError(f"Failed to import {file_path}") from exc
    finally:
        conn.close()
        engine.dispose()


def import_uri(uri: str, **kwargs: Any) -> dict[str, Any]:
    path = _open_uri(uri) if _is_s3_uri(uri) else Path(uri)
    return import_file(str(path), **kwargs)


def main(_args: list[str]) -> tuple[int, int]:
    """Placeholder CLI entrypoint for type checking."""
    return 0, 0
