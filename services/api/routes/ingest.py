from __future__ import annotations

import hashlib
import os
import tempfile
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from urllib.parse import ParseResult, urlparse

import aioboto3
import httpx
import structlog
from botocore.config import Config
from celery import states
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse

from awa_common.files import ALLOWED_UPLOAD_EXTENSIONS, sanitize_upload_name
from awa_common.metrics import (
    ingest_upload_inflight,
    record_ingest_download,
    record_ingest_download_failure,
    record_ingest_upload,
    record_ingest_upload_failure,
)
from awa_common.settings import settings
from etl.load_csv import ImportFileError
from services.api.routes.ingest_errors import IngestRequestError, ingest_error_response, respond_with_ingest_error
from services.api.schemas import ErrorCode
from services.api.security import limit_ops, limit_viewer, require_ops, require_viewer
from services.worker.celery_app import celery_app
from services.worker.tasks import task_import_file

router = APIRouter(prefix="", tags=["ingest"])
logger = structlog.get_logger(__name__)
_SUPPORTED_SUFFIXES = {ext.lower() for ext in ALLOWED_UPLOAD_EXTENSIONS}


def _route_path(request: Request) -> str:
    return str(request.scope.get("path") or request.url.path)


def _unsupported_file_error(filename: str | None) -> IngestRequestError:
    suffix = Path(filename or "").suffix.lower() or "unknown"
    return IngestRequestError(
        status_code=400,
        code="unsupported_file_format",
        detail=f"Files with extension '{suffix}' are not supported",
        hint="Upload CSV or XLSX files exported from Amazon reports.",
    )


def _validate_extension(filename: str | None) -> None:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in _SUPPORTED_SUFFIXES:
        raise _unsupported_file_error(filename)


def _s3_client_kwargs() -> dict[str, Any]:
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    secure = os.getenv("MINIO_SECURE", "false").lower() in {"1", "true", "yes"}
    scheme = "https" if secure else "http"
    return {
        "endpoint_url": f"{scheme}://{endpoint}",
        "aws_access_key_id": os.getenv("MINIO_ACCESS_KEY", "minio"),
        "aws_secret_access_key": os.getenv("MINIO_SECRET_KEY", "minio123"),
        "region_name": os.getenv("AWS_REGION", "us-east-1"),
    }


def _failure_status_and_detail(info: Any) -> tuple[int, str]:
    if isinstance(info, ImportFileError):
        return info.status_code, str(info)
    if isinstance(info, Exception):
        status = getattr(info, "status_code", 500)
        return status, str(info)
    if isinstance(info, dict):
        detail = info.get("error") or info.get("detail") or "ETL ingest failed"
        status = int(info.get("status_code") or 500)
        return status, detail
    return 500, "ETL ingest failed"


def _error_from_failure(info: Any) -> IngestRequestError:
    status, detail = _failure_status_and_detail(info)
    status = status or 500
    code: ErrorCode
    if status == 422:
        code = "unprocessable_entity"
    elif status == 400:
        code = "bad_request"
    elif status == 413:
        code = "bad_request"
    else:
        code = "bad_request"
    return IngestRequestError(status_code=status, code=code, detail=detail)


def _meta_from_result(state: str, info: Any) -> dict[str, Any]:
    if isinstance(info, dict) and (info or state != states.FAILURE):
        return info
    if state == states.FAILURE:
        status, detail = _failure_status_and_detail(info)
        meta: dict[str, Any] = {"status": "error", "error": detail}
        if status:
            meta["status_code"] = status
        return meta
    return {}


@router.post("/ingest")
async def submit_ingest(
    request: Request,
    file: UploadFile | None = File(None),
    uri: str | None = None,
    report_type: str | None = None,
    force: bool = False,
    _: object = Depends(require_ops),
    __: None = Depends(limit_ops),
) -> JSONResponse:
    route = _route_path(request)
    try:
        if not file and uri is None:
            try:
                payload = await request.json()
            except Exception:
                payload = {}
            uri = payload.get("uri")
            report_type = report_type or payload.get("report_type")
            force = force or bool(payload.get("force"))
        if not file and not uri:
            raise IngestRequestError(
                status_code=400,
                code="bad_request",
                detail="Provide a file upload or the uri field.",
                hint="Send multipart/form-data with a file or JSON containing uri.",
            )

        if file:
            try:
                _validate_extension(file.filename)
                tmp_path, idempotency_key = await _persist_upload(file, request=request)
            except IngestRequestError as exc:
                extension = Path(file.filename or "").suffix.lstrip(".") if file and file.filename else "unknown"
                record_ingest_upload_failure(extension=extension, reason=exc.code)
                raise
            resolved_uri = f"file://{tmp_path}"
        else:
            assert uri is not None  # mypy narrow
            tmp_path, idempotency_key = await _download_remote(uri)
            resolved_uri = f"file://{tmp_path}"

        async_result = task_import_file.apply_async(
            args=[resolved_uri],
            kwargs={"report_type": report_type or None, "force": force, "idempotency_key": idempotency_key},
            queue="ingest",
        )
        if celery_app.conf.task_always_eager:
            try:
                async_result.get(propagate=False)
            except Exception:
                pass
            if async_result.failed():
                error = _error_from_failure(async_result.info)
                return respond_with_ingest_error(request, error, route=route)
        return JSONResponse({"task_id": async_result.id})
    except IngestRequestError as exc:
        return respond_with_ingest_error(request, exc, route=route)
    except Exception:
        logger.exception("submit_ingest.failed", route=route)
        return ingest_error_response(
            request,
            status_code=500,
            code="bad_request",
            detail="ETL ingest failed unexpectedly",
            route=route,
        )


@router.get("/jobs/{task_id}")
async def get_job(
    task_id: str,
    _: object = Depends(require_viewer),
    __: None = Depends(limit_viewer),
) -> dict[str, Any]:
    res = celery_app.AsyncResult(task_id)
    try:
        state = res.state
    except Exception:  # pragma: no cover - defensive
        state = states.FAILURE
    try:
        info = res.info
    except Exception:  # pragma: no cover - defensive
        info = {}
    meta = _meta_from_result(state, info)
    return {"task_id": task_id, "state": state, "meta": meta}


async def _persist_upload(file: UploadFile, request: Request) -> tuple[Path, str]:
    if not file.filename:
        raise IngestRequestError(status_code=400, code="bad_request", detail="Uploaded file missing name")
    try:
        safe_name = sanitize_upload_name(file.filename)
    except ValueError as exc:
        message = str(exc)
        if "Unsupported file extension" in message:
            raise _unsupported_file_error(file.filename) from exc
        raise IngestRequestError(status_code=400, code="bad_request", detail=message) from exc
    tmp_dir = Path(tempfile.mkdtemp(prefix="ingest_api_"))
    tmp_path = tmp_dir / safe_name
    chunk_size = max(1, int(settings.INGEST_CHUNK_SIZE_MB) * 1024 * 1024)
    max_bytes = int(settings.MAX_REQUEST_BYTES)
    header = request.headers.get("content-length")
    if header:
        try:
            if int(header) > max_bytes:
                raise IngestRequestError(
                    status_code=413,
                    code="bad_request",
                    detail="Upload exceeds maximum size limit",
                    hint="Split the file or reduce report size and retry.",
                )
        except ValueError:
            pass

    hasher = hashlib.sha256()
    total = 0
    start = time.perf_counter()
    with ingest_upload_inflight():
        with tmp_path.open("wb") as handle:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise IngestRequestError(
                        status_code=413,
                        code="bad_request",
                        detail="Upload exceeds maximum size limit",
                        hint="Split the file or reduce report size and retry.",
                    )
                hasher.update(chunk)
                handle.write(chunk)
    await file.close()
    duration = time.perf_counter() - start
    extension = Path(safe_name).suffix.lstrip(".")
    record_ingest_upload(total, duration, extension=extension)
    return tmp_path, hasher.hexdigest()


async def _download_remote(uri: str) -> tuple[Path, str]:
    parsed = urlparse(uri)
    scheme = (parsed.scheme or "unknown").lower()
    if scheme in {"s3", "minio"}:
        return await _download_minio(parsed)  # pragma: no cover - network path
    if scheme in {"http", "https"}:
        return await _download_http(uri, scheme)  # pragma: no cover - network path
    raise IngestRequestError(
        status_code=400,
        code="bad_request",
        detail=f"Unsupported URI scheme '{scheme}'",
        hint="Use http(s), s3, or minio URIs.",
    )


async def _download_minio(parsed: ParseResult) -> tuple[Path, str]:  # pragma: no cover - network path
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    session = aioboto3.Session()
    config = Config(
        max_pool_connections=settings.S3_MAX_CONNECTIONS,
        connect_timeout=float(settings.ETL_CONNECT_TIMEOUT_S),
        read_timeout=float(settings.ETL_READ_TIMEOUT_S),
    )
    start = time.perf_counter()
    try:
        async with session.client("s3", config=config, **_s3_client_kwargs()) as client:
            response = await client.get_object(Bucket=bucket, Key=key)
            async with response["Body"] as body:
                path, digest, size_bytes = await _write_stream_to_temp(body.iter_chunks(), scheme=parsed.scheme)
    except Exception as exc:
        record_ingest_download_failure(scheme=parsed.scheme, reason=exc.__class__.__name__)
        raise IngestRequestError(
            status_code=502,
            code="bad_request",
            detail="Failed to download source from object storage",
            hint="Verify MinIO/S3 connectivity and credentials.",
        ) from exc
    duration = time.perf_counter() - start
    record_ingest_download(size_bytes, duration, scheme=parsed.scheme)
    return path, digest


async def _download_http(uri: str, scheme: str) -> tuple[Path, str]:  # pragma: no cover - network path
    timeout = httpx.Timeout(connect=settings.ETL_CONNECT_TIMEOUT_S, read=settings.ETL_READ_TIMEOUT_S)
    chunk_size = max(1, int(settings.INGEST_CHUNK_SIZE_MB) * 1024 * 1024)
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("GET", uri, follow_redirects=True) as response:
                response.raise_for_status()

                async def iterator() -> AsyncIterator[bytes]:
                    async for chunk in response.aiter_bytes(chunk_size):
                        yield chunk

                path, digest, size_bytes = await _write_stream_to_temp(iterator(), scheme=scheme)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        record_ingest_download_failure(scheme=scheme, reason=str(status))
        raise IngestRequestError(
            status_code=status,
            code="bad_request",
            detail=f"Failed to download source (HTTP {status})",
        ) from exc
    except httpx.TimeoutException as exc:
        record_ingest_download_failure(scheme=scheme, reason="timeout")
        raise IngestRequestError(
            status_code=504,
            code="bad_request",
            detail="Timeout downloading source",
            hint="Retry later or reduce file size.",
        ) from exc
    except Exception as exc:  # pragma: no cover
        record_ingest_download_failure(scheme=scheme, reason=exc.__class__.__name__)
        raise IngestRequestError(
            status_code=502,
            code="bad_request",
            detail="Failed to download source",
        ) from exc
    duration = time.perf_counter() - start
    record_ingest_download(size_bytes, duration, scheme=scheme)
    return path, digest


async def _write_stream_to_temp(
    chunks: AsyncIterator[bytes], *, scheme: str
) -> tuple[Path, str, int]:  # pragma: no cover - heavy IO exercised via integration
    tmp_dir = Path(tempfile.mkdtemp(prefix="ingest_api_"))
    tmp_path = tmp_dir / "payload.csv"
    max_bytes = int(settings.MAX_REQUEST_BYTES)
    hasher = hashlib.sha256()
    total = 0
    with tmp_path.open("wb") as handle:
        async for chunk in chunks:
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                raise IngestRequestError(
                    status_code=413,
                    code="bad_request",
                    detail="Download exceeds maximum size limit",
                    hint="Limit remote files to MAX_REQUEST_BYTES or upload via MinIO.",
                )
            hasher.update(chunk)
            handle.write(chunk)
    return tmp_path, hasher.hexdigest(), total
