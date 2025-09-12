from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from celery import states
from celery.exceptions import Ignore
from celery.utils.log import get_task_logger

from .celery_app import celery_app

logger = get_task_logger(__name__)


def _download_minio_to_tmp(uri: str) -> Path:
    from urllib.parse import urlparse

    from minio import Minio

    parsed = urlparse(uri)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    secure = os.getenv("MINIO_SECURE", "false").lower() in ("1", "true", "yes")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    client = Minio(
        endpoint, access_key=access_key, secret_key=secret_key, secure=secure
    )
    tmpdir = Path(tempfile.mkdtemp(prefix="ingest_"))
    dst = tmpdir / Path(key).name
    client.fget_object(bucket, key, str(dst))
    return dst


def _resolve_uri_to_path(uri: str) -> Path:
    if uri.startswith("minio://"):
        return _download_minio_to_tmp(uri)
    if uri.startswith("file://"):
        return Path(uri[len("file://") :])
    return Path(uri)


@celery_app.task(name="ingest.import_file", bind=True)  # type: ignore[misc]
def task_import_file(
    self: Any, uri: str, report_type: str | None = None, force: bool = False
) -> dict[str, Any]:
    """Import a file into Postgres using existing ETL pipeline."""

    self.update_state(state=states.STARTED, meta={"stage": "resolve_uri"})
    tmp_dir: Path | None = None
    try:
        local_path = _resolve_uri_to_path(uri)
        if "ingest_" in str(local_path.parent):
            tmp_dir = local_path.parent

        from etl.load_csv import import_file as run_ingest

        self.update_state(state=states.STARTED, meta={"stage": "ingest"})
        result = run_ingest(
            str(local_path),
            report_type=report_type,
            celery_update=lambda m: self.update_state(state=states.STARTED, meta=m),
            force=force,
        )
        summary: dict[str, Any] = {}
        if isinstance(result, dict):
            summary.update(result)
        summary.setdefault("status", "success")
        self.update_state(state=states.SUCCESS, meta=summary)
        return summary
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("task_import_file failed for %s", uri)
        meta = {"status": "error", "error": str(exc)}
        self.update_state(state=states.FAILURE, meta=meta)
        raise Ignore()
    finally:
        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


@celery_app.task(name="ingest.rebuild_views", bind=True)  # type: ignore[misc]
def task_rebuild_views(self: Any) -> dict[str, Any]:
    logger.info("Rebuild views placeholder executed")
    return {"status": "success", "message": "noop"}


if os.getenv("TESTING") == "1":

    @celery_app.task(name="ingest.enqueue_import", bind=True)  # type: ignore[misc]
    def enqueue_import(
        self: Any, *, uri: str, dialect: str
    ) -> dict[str, Any]:  # pragma: no cover - helper for tests
        from etl.load_csv import import_file as run_ingest

        return run_ingest(uri, dialect=dialect)
