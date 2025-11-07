from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from celery import states
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from etl.load_csv import ImportFileError
from services.api.security import limit_ops, limit_viewer, require_ops, require_viewer
from services.worker.celery_app import celery_app
from services.worker.tasks import task_import_file

router = APIRouter(prefix="", tags=["ingest"])


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
) -> dict[str, Any]:
    if not file and uri is None:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        uri = payload.get("uri")
        report_type = report_type or payload.get("report_type")
        force = force or bool(payload.get("force"))
    if not file and not uri:
        raise HTTPException(status_code=400, detail="Provide a file or a uri")

    if file:
        tmp_dir = Path(tempfile.mkdtemp(prefix="ingest_api_"))
        if file.filename is None:
            raise HTTPException(status_code=400, detail="Uploaded file missing name")
        tmp_path = tmp_dir / file.filename
        with tmp_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        uri = f"file://{tmp_path}"
    async_result = task_import_file.apply_async(
        args=[uri],
        kwargs={"report_type": report_type or None, "force": force},
        queue="ingest",
    )
    if celery_app.conf.task_always_eager:
        try:
            async_result.get(propagate=False)
        except Exception:
            pass
        if async_result.failed():
            status, detail = _failure_status_and_detail(async_result.info)
            raise HTTPException(status_code=status, detail=detail)
    return {"task_id": async_result.id}


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
