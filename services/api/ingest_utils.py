from __future__ import annotations

import datetime
import hashlib
import shutil
import tempfile
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any
from urllib.parse import ParseResult, urlparse

import aioboto3
import httpx
import sentry_sdk
import structlog
from fastapi import Request, UploadFile
from fastapi.responses import JSONResponse
from structlog.stdlib import BoundLogger

from awa_common.files import ALLOWED_UPLOAD_EXTENSIONS, sanitize_upload_name
from awa_common.http_client import AsyncHTTPClient, HTTPClientError
from awa_common.metrics import (
    ingest_upload_inflight,
    record_api_ingest_4xx_total,
    record_api_ingest_5xx_total,
    record_ingest_download,
    record_ingest_download_failure,
    record_ingest_upload,
    record_ingest_upload_failure,
)
from awa_common.minio import get_bucket_name, get_s3_client_config, get_s3_client_kwargs
from awa_common.settings import settings
from etl.load_csv import ImportFileError
from services.api.schemas import ErrorCode
from services.api.security import get_request_id
from services.worker.celery_app import celery_app
from services.worker.tasks import task_import_file

logger: BoundLogger = structlog.get_logger(__name__)
_SUPPORTED_SUFFIXES = {ext.lower() for ext in ALLOWED_UPLOAD_EXTENSIONS}
_UPLOAD_TOO_LARGE_DETAIL = "Upload exceeds maximum size limit"
_UPLOAD_TOO_LARGE_HINT = "Split the file or reduce report size and retry."
_DOWNLOAD_TOO_LARGE_DETAIL = "Download exceeds maximum size limit"
_DOWNLOAD_TOO_LARGE_HINT = "Limit remote files to MAX_REQUEST_BYTES or upload via MinIO."


@dataclass
class IngestUpload:
    """Represents an upload that is ready to be ingested."""

    uri: str
    digest: str
    total_bytes: int
    extension: str
    object_key: str | None = None
    path: Path | None = None


class ApiError(Exception):
    """Raised when an ingest or upload request cannot be processed."""

    def __init__(self, *, status_code: int, code: ErrorCode | str, detail: str, hint: str | None = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.hint = hint


def sanitize_filename(name: str) -> tuple[str, str]:
    """Return a sanitized filename and extension or raise an ApiError."""

    if not name:
        raise ApiError(status_code=400, code="bad_request", detail="Filename is required")
    try:
        safe_name = sanitize_upload_name(name)
    except ValueError as exc:
        message = str(exc)
        hint = None
        if "Unsupported file extension" in message:
            code: ErrorCode | str = "unsupported_file_format"
            hint = "Upload CSV or XLSX files exported from Amazon reports."
        else:
            code = "bad_request"
        raise ApiError(status_code=400, code=code, detail=message, hint=hint) from exc

    lowered = safe_name.lower()
    if not any(lowered.endswith(ext) for ext in _SUPPORTED_SUFFIXES):
        suffix = Path(name or "").suffix.lower() or "unknown"
        raise ApiError(
            status_code=400,
            code="unsupported_file_format",
            detail=f"Files with extension '{suffix}' are not supported",
            hint="Upload CSV or XLSX files exported from Amazon reports.",
        )
    extension = Path(safe_name).suffix.lstrip(".") or "unknown"
    return safe_name, extension


async def read_upload_file(
    file: UploadFile,
    *,
    chunk_size: int | None = None,
    max_bytes: int | None = None,
    spool_threshold: int | None = None,
) -> tuple[bytes | Path, str, int, str]:
    """Stream an UploadFile while enforcing limits and hashing content.

    Returns the buffered bytes or a temp file path along with the digest,
    total bytes read, and detected extension.
    """

    safe_name, extension = sanitize_filename(file.filename or "")
    chunk = max(1, int(chunk_size or _upload_limits()[0]))
    ingest_cfg = getattr(settings, "ingestion", None)
    limit = int(
        max_bytes
        if max_bytes is not None
        else (ingest_cfg.max_request_bytes if ingest_cfg else settings.MAX_REQUEST_BYTES)
    )
    spool_default = ingest_cfg.spool_max_bytes if ingest_cfg else getattr(settings, "SPOOL_MAX_BYTES", limit)
    spool_limit = int(spool_threshold if spool_threshold is not None else spool_default)
    hasher = hashlib.sha256()
    total = 0
    buffer = bytearray()
    tmp_path: Path | None = None
    tmp_handle = None
    tmp_dir: Path | None = None
    try:
        while True:
            chunk_bytes = await file.read(chunk)
            if not chunk_bytes:
                break
            total += len(chunk_bytes)
            if total > limit:
                raise ApiError(
                    status_code=413,
                    code="payload_too_large",
                    detail=_UPLOAD_TOO_LARGE_DETAIL,
                    hint=_UPLOAD_TOO_LARGE_HINT,
                )
            hasher.update(chunk_bytes)
            if tmp_path:
                assert tmp_handle is not None
                tmp_handle.write(chunk_bytes)
                continue
            buffer.extend(chunk_bytes)
            if len(buffer) > spool_limit:
                tmp_dir = Path(tempfile.mkdtemp(prefix="ingest_api_"))
                tmp_path = tmp_dir / safe_name
                tmp_handle = tmp_path.open("wb")
                if buffer:
                    tmp_handle.write(buffer)
                    buffer.clear()
        if tmp_handle:
            tmp_handle.flush()
    finally:
        with suppress(Exception):
            if tmp_handle:
                tmp_handle.close()
        with suppress(Exception):
            await file.close()
    payload: bytes | Path = tmp_path if tmp_path is not None else bytes(buffer)
    return payload, hasher.hexdigest(), total, extension


def route_path(request: Request) -> str:
    """Normalize the route path for structured logs."""

    path = request.scope.get("path")
    if isinstance(path, str) and path:
        return path
    try:
        return request.url.path
    except Exception:
        return "/"


def bind_request_logger(request: Request, *, ingest_source: str | None = None) -> BoundLogger:
    """Bind common ingest context to a structlog logger."""

    app_env = getattr(getattr(settings, "app", None), "env", getattr(settings, "ENV", "local"))
    log = logger.bind(route=route_path(request), request_id=get_request_id(request), env=app_env)
    if ingest_source:
        log = log.bind(ingest_source=ingest_source)
    return log


def api_error_response(request: Request, exc: ApiError, *, route: str) -> JSONResponse:
    """Render a structured error response for ingest-style endpoints."""

    request_id = get_request_id(request)
    payload: dict[str, Any] = {"error": {"code": exc.code, "detail": exc.detail}}
    if exc.hint:
        payload["error"]["hint"] = exc.hint
    payload["request_id"] = request_id
    response = JSONResponse(status_code=exc.status_code, content=payload)
    response.headers.setdefault("X-Request-ID", request_id)
    _log_ingest_error(request=request, route=route, status_code=exc.status_code, code=exc.code, detail=exc.detail)
    if 400 <= exc.status_code < 500:
        record_api_ingest_4xx_total(str(exc.code))
    else:
        record_api_ingest_5xx_total()
    return response


def unexpected_error_response(request: Request, *, route: str) -> JSONResponse:
    """Render a generic 500 error while preserving the new error shape."""

    error = ApiError(status_code=500, code="bad_request", detail="ETL ingest failed unexpectedly")
    return api_error_response(request, error, route=route)


def validate_upload_file(file: UploadFile | str) -> tuple[str, str]:
    """Ensure the uploaded filename is safe and uses a supported extension."""

    name = file.filename if isinstance(file, UploadFile) else file
    return sanitize_filename(name or "")


def ensure_size_limit(request: Request, *, max_bytes: int) -> None:
    """Validate the Content-Length header when present."""

    header = request.headers.get("content-length")
    if not header:
        return
    try:
        length = int(header)
    except ValueError:
        return
    if length > max_bytes:
        raise ApiError(
            status_code=413,
            code="payload_too_large",
            detail=_UPLOAD_TOO_LARGE_DETAIL,
            hint=_UPLOAD_TOO_LARGE_HINT,
        )


def enqueue_import_task(upload: IngestUpload, *, report_type: str | None, force: bool, log: BoundLogger) -> Any:
    """Schedule the Celery import task and propagate eager-mode failures as ApiError."""

    async_result = task_import_file.apply_async(
        args=[upload.uri],
        kwargs={"report_type": report_type or None, "force": force, "idempotency_key": upload.digest},
        queue="ingest",
    )
    bound_log = log.bind(task_id=async_result.id, uri=upload.uri)
    if celery_app.conf.task_always_eager:
        try:
            async_result.get(propagate=True)
        except ApiError:
            raise
        except Exception as exc:
            bound_log.warning(
                "ingest_task_get_exception",
                task_state=getattr(async_result, "state", "unknown"),
                error_detail=str(exc),
            )
            sentry_sdk.capture_exception(exc)
        if async_result.failed():
            info = async_result.info
            if isinstance(info, Exception):
                sentry_sdk.capture_exception(info)
            bound_log.error(
                "ingest_task_failed",
                task_state=getattr(async_result, "state", "unknown"),
                error_detail=str(info),
            )
            raise _error_from_failure(info)
    return async_result


async def persist_upload_to_temp(file: UploadFile, request: Request, *, log: BoundLogger) -> IngestUpload:
    """Persist an uploaded file to a temp directory, hashing content as it streams."""

    extension = Path(file.filename or "").suffix.lstrip(".") or "unknown"
    tmp_path: Path | None = None
    try:
        safe_name, extension = validate_upload_file(file)
        chunk_size, max_bytes = _upload_limits()
        ensure_size_limit(request, max_bytes=max_bytes)
        start = time.perf_counter()
        with ingest_upload_inflight():
            payload, digest, total_bytes, extension = await read_upload_file(
                file, chunk_size=chunk_size, max_bytes=max_bytes
            )
            if isinstance(payload, Path):
                tmp_path = payload
            else:
                tmp_dir = Path(tempfile.mkdtemp(prefix="ingest_api_"))
                tmp_path = tmp_dir / safe_name
                with tmp_path.open("wb") as handle:
                    handle.write(payload)
        duration = time.perf_counter() - start
        assert tmp_path is not None
        record_ingest_upload(total_bytes, duration, extension=extension)
        return IngestUpload(
            uri=f"file://{tmp_path}",
            digest=digest,
            total_bytes=total_bytes,
            extension=extension,
            path=tmp_path,
        )
    except ApiError as exc:
        record_ingest_upload_failure(extension=extension, reason=str(exc.code))
        raise
    except Exception as exc:
        record_ingest_upload_failure(extension=extension, reason=exc.__class__.__name__)
        raise
    finally:
        with suppress(Exception):
            await file.close()


async def upload_file_to_minio(file: UploadFile, request: Request, *, log: BoundLogger) -> IngestUpload:
    """Stream an upload directly to MinIO, returning the resulting object URI."""

    extension = Path(file.filename or "").suffix.lstrip(".") or "unknown"
    session = aioboto3.Session()
    payload_path: Path | None = None
    try:
        safe_name, extension = validate_upload_file(file)
        chunk_size, max_bytes = _upload_limits()
        ensure_size_limit(request, max_bytes=max_bytes)
        bucket, key = build_minio_key(safe_name)
        client_kwargs = get_s3_client_kwargs()
        config = get_s3_client_config()
        start = time.perf_counter()
        async with session.client("s3", config=config, **client_kwargs) as client:
            with ingest_upload_inflight():
                payload, digest, total_bytes, extension = await read_upload_file(
                    file, chunk_size=chunk_size, max_bytes=max_bytes
                )
                if isinstance(payload, Path):
                    payload_path = payload
                await _upload_payload_to_minio(
                    client,
                    bucket=bucket,
                    key=key,
                    payload=payload,
                    total_bytes=total_bytes,
                    chunk_size=chunk_size,
                )
        duration = time.perf_counter() - start
        record_ingest_upload(total_bytes, duration, extension=extension)
        return IngestUpload(
            uri=f"minio://{bucket}/{key}",
            digest=digest,
            total_bytes=total_bytes,
            extension=extension,
            object_key=key,
        )
    except ApiError as exc:
        record_ingest_upload_failure(extension=extension, reason=str(exc.code))
        raise
    except Exception as exc:
        record_ingest_upload_failure(extension=extension, reason=exc.__class__.__name__)
        raise
    finally:
        with suppress(Exception):
            await file.close()
        if payload_path:
            shutil.rmtree(payload_path.parent, ignore_errors=True)


async def download_uri_to_temp(uri: str, *, log: BoundLogger) -> IngestUpload:
    """Download an HTTP, HTTPS, S3/MinIO, or file URI to a temp file with size enforcement."""

    parsed = urlparse(uri)
    scheme = (parsed.scheme or "unknown").lower()
    if scheme in {"s3", "minio"}:
        return await _download_minio(parsed)
    if scheme in {"http", "https"}:
        return await _download_http(uri, scheme)
    if scheme in {"file", ""}:
        return await _download_file(parsed)
    raise ApiError(
        status_code=400,
        code="bad_request",
        detail=f"Unsupported URI scheme '{scheme}'",
        hint="Use http(s), s3, or minio URIs.",
    )


def _upload_limits() -> tuple[int, int]:
    try:
        settings.__dict__.pop("ingestion", None)
    except Exception:
        pass
    ingest_cfg = getattr(settings, "ingestion", None)
    chunk_mb = ingest_cfg.chunk_size_mb if ingest_cfg else getattr(settings, "INGEST_CHUNK_SIZE_MB", 8)
    max_bytes = ingest_cfg.max_request_bytes if ingest_cfg else getattr(settings, "MAX_REQUEST_BYTES", 268_435_456)
    chunk_size = max(1, int(chunk_mb) * 1024 * 1024)
    return chunk_size, int(max_bytes)


async def _upload_payload_to_minio(
    client: Any,
    *,
    bucket: str,
    key: str,
    payload: bytes | Path,
    total_bytes: int,
    chunk_size: int,
) -> None:
    part_size = max(1, int(chunk_size))
    upload_id: str | None = None
    parts: list[dict[str, Any]] = []
    handle: IO[bytes] | None = None
    iterator: Iterator[bytes]
    try:
        if isinstance(payload, Path):
            handle = payload.open("rb")
        else:
            handle = None
        if total_bytes <= part_size:
            if isinstance(payload, bytes):
                body = payload
            else:
                assert handle is not None
                body = handle.read()
            await client.put_object(Bucket=bucket, Key=key, Body=body)
            return

        if isinstance(payload, bytes):
            iterator = (payload[i : i + part_size] for i in range(0, len(payload), part_size))
        else:
            assert handle is not None
            iterator = iter(lambda: handle.read(part_size), b"")
        upload = await client.create_multipart_upload(Bucket=bucket, Key=key)
        upload_id = upload["UploadId"]
        for part_no, data in enumerate(iterator, start=1):
            response = await client.upload_part(
                Bucket=bucket, Key=key, UploadId=upload_id, PartNumber=part_no, Body=data
            )
            parts.append({"ETag": response["ETag"], "PartNumber": part_no})
        await client.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
    except Exception as exc:
        if upload_id:
            with suppress(Exception):
                await client.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id)
        raise ApiError(
            status_code=500,
            code="bad_request",
            detail="Failed to upload file to object storage",
        ) from exc
    finally:
        if handle:
            handle.close()


async def _download_minio(parsed: ParseResult) -> IngestUpload:
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    session = aioboto3.Session()
    config = get_s3_client_config()
    start = time.perf_counter()
    try:
        async with session.client("s3", config=config, **get_s3_client_kwargs()) as client:
            response = await client.get_object(Bucket=bucket, Key=key)
            async with response["Body"] as body:
                path, digest, size_bytes = await _write_stream_to_temp(body.iter_chunks(), scheme=parsed.scheme)
    except ApiError:
        raise
    except Exception as exc:
        record_ingest_download_failure(scheme=parsed.scheme, reason=exc.__class__.__name__)
        raise ApiError(
            status_code=502,
            code="bad_request",
            detail="Failed to download source from object storage",
            hint="Verify MinIO/S3 connectivity and credentials.",
        ) from exc
    duration = time.perf_counter() - start
    record_ingest_download(size_bytes, duration, scheme=parsed.scheme)
    extension = Path(key).suffix.lstrip(".") or "unknown"
    return IngestUpload(
        uri=f"file://{path}",
        digest=digest,
        total_bytes=size_bytes,
        extension=extension,
        path=path,
    )


async def _download_http(uri: str, scheme: str) -> IngestUpload:
    etl_cfg = getattr(settings, "etl", None)
    total_timeout = float(etl_cfg.total_timeout_s if etl_cfg else settings.HTTP_TOTAL_TIMEOUT_S)
    connect_timeout = float(etl_cfg.connect_timeout_s if etl_cfg else settings.HTTP_CONNECT_TIMEOUT_S)
    read_timeout = float(etl_cfg.read_timeout_s if etl_cfg else settings.HTTP_READ_TIMEOUT_S)
    timeout = httpx.Timeout(
        timeout=total_timeout,
        connect=connect_timeout,
        read=read_timeout,
        write=read_timeout,
    )
    chunk_size, _ = _upload_limits()
    start = time.perf_counter()
    response: httpx.Response | None = None
    try:
        async with AsyncHTTPClient(
            integration="ingest_download",
            timeout=timeout,
            total_timeout_s=total_timeout,
        ) as client:
            response = await client.request("GET", uri, follow_redirects=True, timeout=timeout)

            async def iterator() -> AsyncIterator[bytes]:
                assert response is not None
                async for chunk in response.aiter_bytes(chunk_size):
                    yield chunk

            path, digest, size_bytes = await _write_stream_to_temp(iterator(), scheme=scheme)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        record_ingest_download_failure(scheme=scheme, reason=str(status))
        raise ApiError(
            status_code=status,
            code="bad_request",
            detail=f"Failed to download source (HTTP {status})",
        ) from exc
    except httpx.TimeoutException as exc:
        record_ingest_download_failure(scheme=scheme, reason="timeout")
        raise ApiError(
            status_code=504,
            code="bad_request",
            detail="Timeout downloading source",
            hint="Retry later or reduce file size.",
        ) from exc
    except ApiError:
        raise
    except HTTPClientError as exc:
        record_ingest_download_failure(scheme=scheme, reason=exc.__class__.__name__)
        raise ApiError(
            status_code=502,
            code="bad_request",
            detail="Failed to download source",
        ) from exc
    except Exception as exc:
        record_ingest_download_failure(scheme=scheme, reason=exc.__class__.__name__)
        raise ApiError(
            status_code=502,
            code="bad_request",
            detail="Failed to download source",
        ) from exc
    finally:
        if response is not None:
            close = getattr(response, "aclose", None)
            if callable(close):
                await close()
            elif hasattr(response, "close"):
                response.close()
    duration = time.perf_counter() - start
    record_ingest_download(size_bytes, duration, scheme=scheme)
    extension = Path(urlparse(uri).path).suffix.lstrip(".") or "unknown"
    return IngestUpload(
        uri=f"file://{path}",
        digest=digest,
        total_bytes=size_bytes,
        extension=extension,
        path=path,
    )


async def _download_file(parsed: ParseResult) -> IngestUpload:
    target = Path(parsed.path or "")
    if not target.exists() or not target.is_file():
        raise ApiError(status_code=400, code="bad_request", detail="File URI does not exist or is unreadable")
    chunk_size, max_bytes = _upload_limits()
    hasher = hashlib.sha256()
    total = 0
    tmp_dir = Path(tempfile.mkdtemp(prefix="ingest_api_"))
    tmp_path = tmp_dir / target.name
    with tmp_path.open("wb") as handle:
        with target.open("rb") as source:
            while True:
                chunk = source.read(chunk_size)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ApiError(
                        status_code=413,
                        code="payload_too_large",
                        detail=_DOWNLOAD_TOO_LARGE_DETAIL,
                        hint=_DOWNLOAD_TOO_LARGE_HINT,
                    )
                hasher.update(chunk)
                handle.write(chunk)
    extension = target.suffix.lstrip(".") or "unknown"
    return IngestUpload(
        uri=f"file://{tmp_path}",
        digest=hasher.hexdigest(),
        total_bytes=total,
        extension=extension,
        path=tmp_path,
    )


async def _write_stream_to_temp(chunks: AsyncIterator[bytes], *, scheme: str) -> tuple[Path, str, int]:
    tmp_dir = Path(tempfile.mkdtemp(prefix="ingest_api_"))
    tmp_path = tmp_dir / "payload.csv"
    ingest_cfg = getattr(settings, "ingestion", None)
    max_bytes = int(ingest_cfg.max_request_bytes if ingest_cfg else getattr(settings, "MAX_REQUEST_BYTES", 268_435_456))
    hasher = hashlib.sha256()
    total = 0
    with tmp_path.open("wb") as handle:
        async for chunk in chunks:
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                raise ApiError(
                    status_code=413,
                    code="payload_too_large",
                    detail=_DOWNLOAD_TOO_LARGE_DETAIL,
                    hint=_DOWNLOAD_TOO_LARGE_HINT,
                )
            hasher.update(chunk)
            handle.write(chunk)
    return tmp_path, hasher.hexdigest(), total


def build_minio_key(filename: str) -> tuple[str, str]:
    bucket = get_bucket_name()
    today = datetime.date.today().strftime("%Y-%m")
    key = f"raw/amazon/{today}/{filename}"
    return bucket, key


def _log_ingest_error(*, request: Request, route: str, status_code: int, code: ErrorCode | str, detail: str) -> None:
    user_sub = getattr(getattr(request.state, "user", None), "sub", None)
    bound = logger.bind(route=route, request_id=get_request_id(request), user_sub=user_sub)
    log = bound.warning if status_code < 500 else bound.error
    log(
        "ingest_error",
        error_code=code,
        error_detail=detail,
        status_code=status_code,
    )


def _failure_status_and_detail(info: Any) -> tuple[int, str]:
    if isinstance(info, ImportFileError):
        return getattr(info, "status_code", 500), str(info)
    if isinstance(info, Exception):
        status = getattr(info, "status_code", 500)
        return status or 500, str(info)
    if isinstance(info, dict):
        detail = info.get("error") or info.get("detail") or "ETL ingest failed"
        status = int(info.get("status_code") or 500)
        return status, detail
    return 500, "ETL ingest failed"


def _error_from_failure(info: Any) -> ApiError:
    status, detail = _failure_status_and_detail(info)
    status = status or 500
    if status == 422:
        code: ErrorCode | str = "unprocessable_entity"
    elif status == 413:
        code = "payload_too_large"
    elif status == 400:
        code = "bad_request"
    else:
        code = "bad_request"
    return ApiError(status_code=status, code=code, detail=detail)


def meta_from_result(state: str, info: Any) -> dict[str, Any]:
    from celery import states

    if isinstance(info, dict) and (info or state != states.FAILURE):
        return info
    if state == states.FAILURE:
        status, detail = _failure_status_and_detail(info)
        meta: dict[str, Any] = {"status": "error", "error": detail}
        if status:
            meta["status_code"] = status
        return meta
    return {}


# Backwards-compatible alias for legacy imports
IngestRequestError = ApiError
respond_with_ingest_error = api_error_response
ingest_error_response = api_error_response

__all__ = [
    "ApiError",
    "build_minio_key",
    "IngestRequestError",
    "IngestUpload",
    "api_error_response",
    "bind_request_logger",
    "download_uri_to_temp",
    "ensure_size_limit",
    "enqueue_import_task",
    "ingest_error_response",
    "meta_from_result",
    "persist_upload_to_temp",
    "read_upload_file",
    "respond_with_ingest_error",
    "route_path",
    "sanitize_filename",
    "unexpected_error_response",
    "upload_file_to_minio",
    "validate_upload_file",
]
