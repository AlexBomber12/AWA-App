from __future__ import annotations

from contextlib import suppress

import sentry_sdk
from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import JSONResponse

from services.api.ingest_utils import (
    ApiError,
    api_error_response,
    bind_request_logger,
    enqueue_import_task,
    route_path,
    unexpected_error_response,
    upload_file_to_minio,
)
from services.api.security import limit_ops, require_ops

router = APIRouter()


@router.post("/", status_code=202)
async def upload(
    request: Request,
    file: UploadFile,
    _: object = Depends(require_ops),
    __: None = Depends(limit_ops),
) -> JSONResponse:
    route = route_path(request)
    log = bind_request_logger(request, ingest_source="upload")
    log.info("upload_legacy_entrypoint", hint="Use /ingest for new callers.")
    try:
        upload_target = await upload_file_to_minio(file, request=request, log=log)
        async_result = enqueue_import_task(upload_target, report_type=None, force=False, log=log)
        return JSONResponse(
            status_code=202,
            content={
                "task_id": async_result.id,
                "object_key": upload_target.object_key,
                "idempotency_key": upload_target.digest,
            },
        )
    except ApiError as exc:
        return api_error_response(request, exc, route=route)
    except Exception as exc:
        log.exception("upload.failed")
        sentry_sdk.capture_exception(exc)
        return unexpected_error_response(request, route=route)
    finally:
        with suppress(Exception):
            await file.close()
