from __future__ import annotations

import asyncio
import csv
import io
import logging
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any
from urllib.parse import parse_qs, urlparse

import anyio
import httpx
from httpx import HTTPStatusError

URL = os.getenv("FREIGHT_API_URL", "https://example.com/freight.csv")

__all__ = [
    "URL",
    "UnsupportedExcelError",
    "fetch_rates",
    "fetch_sources",
]

logger = logging.getLogger(__name__)


class UnsupportedExcelError(RuntimeError):
    """Raised when an Excel payload cannot be parsed due to missing optional deps."""


@dataclass
class SourcePayload:
    source: str
    raw: bytes
    meta: dict[str, Any]
    rows: list[dict[str, Any]]
    error: Exception | None = None


def _timeout_setting() -> int:
    try:
        return int(os.getenv("LOGISTICS_TIMEOUT_S", "15"))
    except ValueError:
        return 15


def _retry_setting() -> int:
    try:
        return int(os.getenv("LOGISTICS_RETRIES", "3"))
    except ValueError:
        return 3


async def fetch_sources() -> list[dict[str, Any]]:
    """
    Fetch logistics rate sources configured via LOGISTICS_SOURCES.

    Returns a list of dictionaries each containing:
        source, raw (bytes), meta (dict), rows (normalized list), error (Exception|None)
    """
    sources_env = os.getenv("LOGISTICS_SOURCES", "")
    uris = [s.strip() for s in sources_env.split(",") if s.strip()]
    if not uris:
        return []

    timeout_s = _timeout_setting()
    retries = _retry_setting()
    snapshots: list[SourcePayload] = []

    for uri in uris:
        try:
            raw, meta = await _download_with_retries(uri, timeout_s=timeout_s, retries=retries)
            rows = _parse_rows(uri, raw, meta)
            snapshots.append(SourcePayload(uri, raw, meta, rows))
        except UnsupportedExcelError as exc:
            logger.warning("Excel support unavailable for %s: %s", uri, exc)
            snapshots.append(SourcePayload(uri, b"", {}, [], exc))
        except Exception as exc:  # pragma: no cover - logged for observability
            logger.exception("Failed to fetch logistics source %s", uri)
            snapshots.append(SourcePayload(uri, b"", {}, [], exc))

    return [asdict(snap) for snap in snapshots]


async def fetch_rates() -> list[dict[str, object]]:
    """
    Backward-compatible shim used by legacy callers.
    Downloads the single FREIGHT_API_URL CSV and returns parsed rows.
    """
    url = URL
    if not url:
        return []

    try:
        raw, _ = await _download_with_retries(url, timeout_s=_timeout_setting(), retries=_retry_setting())
    except Exception:
        return []

    if not raw:
        return []

    try:
        text_content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text_content = raw.decode("utf-8", errors="ignore")

    reader = csv.DictReader(io.StringIO(text_content))
    rows: list[dict[str, object]] = []
    for row in reader:
        value = row.get("eur_per_kg", 0)
        try:
            row["eur_per_kg"] = float(value)
        except (TypeError, ValueError):
            row["eur_per_kg"] = 0.0
        rows.append(dict(row))
    return rows


async def _download_with_retries(  # noqa: C901
    url_or_uri: str, *, timeout_s: int, retries: int
) -> tuple[bytes, dict[str, Any]]:
    parsed = urlparse(url_or_uri)
    scheme = (parsed.scheme or "").lower()
    attempt = 0
    backoff = 0.5
    last_error: Exception | None = None

    while attempt <= retries:
        try:
            if scheme in ("http", "https"):
                return await _download_http(url_or_uri, timeout_s)
            if scheme == "s3":
                return await _download_s3(parsed, timeout_s)
            if scheme == "ftp":
                return await _download_ftp(parsed, timeout_s)
            raise ValueError(f"Unsupported logistics source scheme: {scheme or 'unknown'}")
        except HTTPStatusError as exc:
            status = exc.response.status_code
            if 500 <= status < 600 and attempt < retries:
                last_error = exc
            else:
                raise
        except Exception as exc:
            last_error = exc
        if attempt >= retries:
            if last_error:
                raise last_error
            raise RuntimeError("Download failed without captured exception")
        await asyncio.sleep(min(8.0, backoff))
        backoff *= 2
        attempt += 1

    if last_error:  # pragma: no cover - defensive, loop should have returned/raised
        raise last_error
    raise RuntimeError("Download failed without captured exception")


async def _download_http(url: str, timeout_s: int) -> tuple[bytes, dict[str, Any]]:
    async with httpx.AsyncClient(timeout=timeout_s, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        etag = response.headers.get("etag")
        meta = {
            "content_type": response.headers.get("content-type"),
            "etag": etag.strip('"') if etag else None,
            "last_modified": response.headers.get("last-modified"),
        }
        seqno = response.headers.get("x-amz-version-id") or meta.get("etag")
        if seqno:
            meta["seqno"] = seqno.strip('"')
        return response.content, meta


async def _download_s3(parsed, timeout_s: int) -> tuple[bytes, dict[str, Any]]:
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    extra: dict[str, Any] = {}
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        version_id = params.get("versionId") or params.get("versionid")
        if version_id:
            extra["VersionId"] = version_id[0]

    def _get() -> tuple[bytes, dict[str, Any]]:
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except Exception as exc:  # pragma: no cover - boto3 optional in tests
            raise RuntimeError("boto3 is required for S3 logistics sources") from exc

        client = boto3.client("s3")
        try:
            response = client.get_object(Bucket=bucket, Key=key, **extra)
        except (
            BotoCoreError,
            ClientError,
        ) as exc:  # pragma: no cover - bubbled to retry
            raise RuntimeError(str(exc)) from exc
        body = response["Body"].read()
        meta = {
            "etag": (response.get("ETag") or "").strip('"') or None,
            "last_modified": None,
            "content_type": response.get("ContentType"),
            "seqno": response.get("VersionId"),
        }
        last_modified = response.get("LastModified")
        if last_modified:
            if isinstance(last_modified, datetime):
                meta["last_modified"] = last_modified.isoformat()
            else:
                meta["last_modified"] = str(last_modified)
        if not meta.get("seqno") and meta.get("etag"):
            meta["seqno"] = meta["etag"]
        return body, meta

    return await anyio.to_thread.run_sync(_get, limiter=None)


async def _download_ftp(parsed, timeout_s: int) -> tuple[bytes, dict[str, Any]]:
    path = parsed.path.lstrip("/")
    host = parsed.hostname
    if not host:
        raise ValueError("FTP source missing hostname")
    port = parsed.port or 21
    username = parsed.username or "anonymous"
    password = parsed.password or "anonymous@"

    def _get() -> tuple[bytes, dict[str, Any]]:
        from ftplib import FTP

        buf = io.BytesIO()
        meta: dict[str, Any] = {}
        with FTP() as ftp:
            ftp.connect(host, port, timeout=timeout_s)
            ftp.login(username, password)
            ftp.retrbinary(f"RETR {path}", buf.write)
            try:
                stat = ftp.sendcmd(f"MDTM {path}")
                if stat.startswith("213"):
                    timestamp = stat.split()[1]
                    meta["last_modified"] = timestamp
                    meta["seqno"] = timestamp
            except Exception:  # pragma: no cover - optional metadata
                pass
        return buf.getvalue(), meta

    return await anyio.to_thread.run_sync(_get, limiter=None)


def _parse_rows(source: str, raw: bytes, meta: dict[str, Any]) -> list[dict[str, Any]]:
    if not raw:
        return []
    hint = meta.get("content_type") or source
    fmt = _detect_format(raw, hint)
    if fmt == "csv":
        return _parse_csv_rows(source, raw)
    if fmt == "excel":
        return _parse_excel_rows(source, raw)
    raise ValueError(f"Unsupported data format for {source}")


def _detect_format(raw_bytes: bytes, name_or_ct: str | None) -> str:
    hint = (name_or_ct or "").lower()
    if ".csv" in hint or "text/csv" in hint:
        return "csv"
    if any(ext in hint for ext in (".xlsx", ".xls", "spreadsheet", "ms-excel")):
        return "excel"
    # Fallback: try sniffing CSV
    try:
        sample = raw_bytes[:1024].decode("utf-8-sig")
        csv.Sniffer().sniff(sample)
        return "csv"
    except Exception:
        return "excel"


def _parse_csv_rows(source: str, raw: bytes) -> list[dict[str, Any]]:
    text = raw.decode("utf-8-sig")
    buf = io.StringIO(text)
    try:
        dialect = csv.Sniffer().sniff(text[:1024])
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(buf, dialect=dialect)
    rows: list[dict[str, Any]] = []
    for row in reader:
        try:
            rows.append(_normalize_row(row, source))
        except ValueError as exc:
            logger.warning("Skipping invalid row from %s: %s", source, exc)
    return rows


def _parse_excel_rows(source: str, raw: bytes) -> list[dict[str, Any]]:
    try:
        from openpyxl import load_workbook  # type: ignore[import]
    except Exception as exc:
        raise UnsupportedExcelError("openpyxl is required to process Excel logistics sources") from exc

    stream = io.BytesIO(raw)
    wb = load_workbook(stream, read_only=True, data_only=True)
    ws = wb.active
    rows: list[dict[str, Any]] = []
    headers: list[str] = []
    for idx, row in enumerate(ws.iter_rows(values_only=True)):
        values = list(row)
        if idx == 0:
            headers = [str(v).strip() if v is not None else "" for v in values]
            continue
        data = {headers[i]: values[i] for i in range(min(len(headers), len(values)))}
        try:
            rows.append(_normalize_row(data, source))
        except ValueError as exc:
            logger.warning("Skipping invalid Excel row from %s: %s", source, exc)
    return rows


def _normalize_row(row: dict[str, Any], source: str) -> dict[str, Any]:  # noqa: C901
    normalized = {((k or "").strip().lower()): v for k, v in row.items()}

    def _as_str(*keys: str) -> str:
        for key in keys:
            value = normalized.get(key)
            if value is None:
                continue
            if isinstance(value, str):
                value = value.strip()
            return str(value).strip()
        raise ValueError(f"Missing required field {keys} in source {source}")

    def _optional_str(*keys: str) -> str | None:
        try:
            raw_value = _as_str(*keys)
        except ValueError:
            return None
        return raw_value or None

    def _as_float(*keys: str) -> float:
        for key in keys:
            value = normalized.get(key)
            if value is None or value == "":
                continue
            try:
                return float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid float for {key}: {value}") from exc
        raise ValueError(f"Missing float field {keys} in source {source}")

    def _as_date(*keys: str) -> str | None:
        raw_value = _optional_str(*keys)
        if raw_value is None:
            return None
        try:
            return _normalize_date(raw_value)
        except ValueError as exc:
            raise ValueError(f"Invalid date value {raw_value} for keys {keys}") from exc

    carrier = _as_str("carrier", "carrier_name", "carrier code")
    origin = _as_str("origin", "origin_code", "from")
    dest = _as_str("dest", "destination", "destination_code", "to")
    service = _as_str("service", "service_level", "mode")
    eur_per_kg = _as_float("eur_per_kg", "rate", "price_per_kg")
    effective_from = _as_date("effective_from", "valid_from", "start_date")
    effective_to = _as_date("effective_to", "valid_to", "end_date")

    return {
        "carrier": carrier,
        "origin": origin,
        "dest": dest,
        "service": service,
        "eur_per_kg": eur_per_kg,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "source": source,
    }


def _normalize_date(value: str | date | datetime) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        raise ValueError("Empty date value")

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        # fromisoformat supports YYYY-MM-DD and other ISO variants
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError as exc:
        raise ValueError(f"Unrecognized date format: {text}") from exc
