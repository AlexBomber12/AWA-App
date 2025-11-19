from __future__ import annotations

import datetime
import hashlib
import time
from collections.abc import AsyncIterator
from contextlib import suppress
from pathlib import Path
from typing import Any

import aioboto3
import sentry_sdk
import structlog
from botocore.config import Config
from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import JSONResponse

from awa_common.files import sanitize_upload_name
from awa_common.metrics import ingest_upload_inflight, record_ingest_upload, record_ingest_upload_failure
from awa_common.minio import get_bucket_name, get_s3_client_kwargs
from awa_common.settings import settings
from services.api.routes.ingest_errors import IngestRequestError, ingest_error_response, respond_with_ingest_error
from services.api.security import get_request_id, limit_ops, require_ops
from services.worker.celery_app import celery_app
from services.worker.tasks import task_import_file

BUCKET = get_bucket_name()
router = APIRouter()
logger = structlog.get_logger(__name__)


def _route_path(request: Request) -> str:
    path = request.scope.get("path")
    if isinstance(path, str) and path:
        return path
    try:
        return request.url.path
    except KeyError:
        return "/"


async def _iter_upload_chunks(upload: UploadFile, chunk_size: int) -> AsyncIterator[bytes]:
    while True:
        chunk = await upload.read(chunk_size)
        if not chunk:
            break
        yield chunk


async def _upload_stream_to_s3(  # pragma: no cover - exercised via integration tests
    file: UploadFile,
    *,
    key: str,
    chunk_size: int,
    max_bytes: int,
) -> tuple[int, str]:
    hasher = hashlib.sha256()
    total = 0

    async def _chunk_source() -> AsyncIterator[bytes]:
        nonlocal total
        async for chunk in _iter_upload_chunks(file, chunk_size):
            total += len(chunk)
            if total > max_bytes:
                raise IngestRequestError(
                    status_code=413,
                    code="bad_request",
                    detail="Upload exceeds maximum size limit",
                    hint="Split the file or reduce report size and retry.",
                )
            hasher.update(chunk)
            yield chunk

    session = aioboto3.Session()
    client_kwargs = get_s3_client_kwargs()
    config = Config(
        max_pool_connections=settings.S3_MAX_CONNECTIONS,
        connect_timeout=float(settings.ETL_CONNECT_TIMEOUT_S),
        read_timeout=float(settings.ETL_READ_TIMEOUT_S),
    )
    async with session.client("s3", config=config, **client_kwargs) as client:
        upload_id: str | None = None
        parts: list[dict[str, Any]] = []
        part_no = 1
        buffer = bytearray()

        async def _flush_part(payload: bytes, number: int) -> None:
            nonlocal parts
            response = await client.upload_part(
                Bucket=BUCKET,
                Key=key,
                UploadId=upload_id,
                PartNumber=number,
                Body=payload,
            )
            parts.append({"ETag": response["ETag"], "PartNumber": number})

        try:
            async for chunk in _chunk_source():
                buffer.extend(chunk)
                if upload_id is None and len(buffer) >= chunk_size:
                    upload = await client.create_multipart_upload(Bucket=BUCKET, Key=key)
                    upload_id = upload["UploadId"]
                while upload_id and len(buffer) >= chunk_size:
                    payload = bytes(buffer[:chunk_size])
                    del buffer[:chunk_size]
                    await _flush_part(payload, part_no)
                    part_no += 1
            if upload_id is None:
                await client.put_object(Bucket=BUCKET, Key=key, Body=bytes(buffer))
            else:
                if buffer:
                    await _flush_part(bytes(buffer), part_no)
                await client.complete_multipart_upload(
                    Bucket=BUCKET,
                    Key=key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": parts},
                )
        except Exception as exc:
            if upload_id:
                with suppress(Exception):
                    await client.abort_multipart_upload(Bucket=BUCKET, Key=key, UploadId=upload_id)
            raise IngestRequestError(
                status_code=500,
                code="bad_request",
                detail="Failed to upload file to object storage",
            ) from exc

    return total, hasher.hexdigest()


def _ensure_size_limit(request: Request, *, max_bytes: int) -> None:
    header = request.headers.get("content-length")
    if not header:
        return
    try:
        length = int(header)
    except ValueError:
        return
    if length > max_bytes:
        raise IngestRequestError(
            status_code=413,
            code="bad_request",
            detail="Upload exceeds maximum size limit",
            hint="Split the file or reduce report size and retry.",
        )


@router.post("/", status_code=202)
async def upload(
    request: Request,
    file: UploadFile,
    _: object = Depends(require_ops),
    __: None = Depends(limit_ops),
) -> JSONResponse:
    route = _route_path(request)
    request_id = get_request_id(request)
    app_env = getattr(getattr(settings, "app", None), "env", getattr(settings, "ENV", "local"))
    log = logger.bind(route=route, request_id=request_id, env=app_env)
    start = time.perf_counter()
    total_bytes = 0
    idempotency_key: str | None = None
    try:
        if not file.filename:
            raise IngestRequestError(
                status_code=400,
                code="bad_request",
                detail="Filename is required",
            )
        try:
            safe_name = sanitize_upload_name(file.filename)
        except ValueError as exc:
            message = str(exc)
            code = "unsupported_file_format" if "Unsupported file extension" in message else "bad_request"
            raise IngestRequestError(status_code=400, code=code, detail=message) from exc

        max_bytes = int(settings.MAX_REQUEST_BYTES)
        _ensure_size_limit(request, max_bytes=max_bytes)
        chunk_size = max(1, int(settings.INGEST_CHUNK_SIZE_MB) * 1024 * 1024)
        today = datetime.date.today().strftime("%Y-%m")
        key = f"raw/amazon/{today}/{safe_name}"
        extension = Path(safe_name).suffix.lstrip(".") or "unknown"

        with ingest_upload_inflight():
            try:
                total_bytes, idempotency_key = await _upload_stream_to_s3(
                    file,
                    key=key,
                    chunk_size=chunk_size,
                    max_bytes=max_bytes,
                )
            except IngestRequestError as exc:
                record_ingest_upload_failure(extension=extension, reason=exc.code)
                raise
            except Exception as exc:  # pragma: no cover - defensive
                record_ingest_upload_failure(extension=extension, reason=exc.__class__.__name__)
                raise IngestRequestError(
                    status_code=500,
                    code="bad_request",
                    detail="Failed to upload file",
                ) from exc

        duration = time.perf_counter() - start
        record_ingest_upload(total_bytes, duration, extension=extension)

        async_result = task_import_file.apply_async(
            args=[f"minio://{key}"],
            kwargs={"report_type": None, "force": False, "idempotency_key": idempotency_key},
            queue="ingest",
        )
        if celery_app.conf.task_always_eager:
            try:
                async_result.get(propagate=False)
            except Exception:
                pass
        return JSONResponse(
            status_code=202,
            content={
                "task_id": async_result.id,
                "object_key": key,
                "idempotency_key": idempotency_key,
            },
        )
    except IngestRequestError as exc:
        return respond_with_ingest_error(request, exc, route=route)
    except Exception as exc:
        log.exception("upload.failed")
        sentry_sdk.capture_exception(exc)
        return ingest_error_response(
            request,
            status_code=500,
            code="bad_request",
            detail="Failed to enqueue upload",
            route=route,
        )
    finally:
        with suppress(Exception):
            await file.close()
