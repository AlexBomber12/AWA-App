from __future__ import annotations

from typing import Any

import sentry_sdk
from celery import states
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse

from services.api.ingest_utils import (
    ApiError,
    api_error_response,
    bind_request_logger,
    download_uri_to_temp,
    enqueue_import_task,
    meta_from_result,
    persist_upload_to_temp,
    route_path,
    unexpected_error_response,
)
from services.api.security import limit_ops, limit_viewer, require_ops, require_viewer
from services.worker.celery_app import celery_app

router = APIRouter(prefix="", tags=["ingest"])


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
    route = route_path(request)
    ingest_source = "upload" if file else "uri"
    log = bind_request_logger(request, ingest_source=ingest_source)
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
            raise ApiError(
                status_code=400,
                code="bad_request",
                detail="Provide a file upload or the uri field.",
                hint="Send multipart/form-data with a file or JSON containing uri.",
            )

        if file:
            upload = await persist_upload_to_temp(file, request=request, log=log)
        else:
            assert uri is not None  # mypy narrow
            upload = await download_uri_to_temp(uri, log=log)

        log = log.bind(uri=upload.uri)
        async_result = enqueue_import_task(upload, report_type=report_type, force=force, log=log)
        return JSONResponse({"task_id": async_result.id})
    except ApiError as exc:
        return api_error_response(request, exc, route=route)
    except Exception as exc:
        log.exception("submit_ingest.failed")
        sentry_sdk.capture_exception(exc)
        return unexpected_error_response(request, route=route)


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
    meta = meta_from_result(state, info)
    return {"task_id": task_id, "state": state, "meta": meta}
