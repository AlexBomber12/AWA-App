from __future__ import annotations

import asyncio
import importlib
import os
import shutil
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import aioboto3
import structlog
from celery import states

from awa_common.metrics import (
    instrument_task as _instrument_task,
    record_ingest_task_failure,
    record_ingest_task_mode,
    record_ingest_task_outcome,
)
from awa_common.minio import get_s3_client_config, get_s3_client_kwargs
from awa_common.settings import settings
from services.alert_bot import worker as alerts_worker
from services.worker.celery_app import celery_app


def _fallback_async_to_sync(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(func(*args, **kwargs))

    return wrapper


try:  # pragma: no cover - fallback when asgiref is missing
    from asgiref.sync import async_to_sync as _asu_async_to_sync

    _asgiref_async_to_sync: Callable[..., Any] | None = _asu_async_to_sync
except ModuleNotFoundError:  # pragma: no cover - allows tests without asgiref
    _asgiref_async_to_sync = None


def _resolve_async_to_sync() -> Callable[..., Any]:
    if _asgiref_async_to_sync is not None:
        return _asgiref_async_to_sync
    try:
        module = importlib.import_module("asgiref.sync")
        func = getattr(module, "async_to_sync", None)
        if func is None:
            raise AttributeError("async_to_sync missing")
        return cast(Callable[..., Any], func)
    except (ModuleNotFoundError, AttributeError):  # pragma: no cover - executed in fallback tests
        return _fallback_async_to_sync


async_to_sync = _resolve_async_to_sync()

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Protocol, TypeVar

    _InstrumentFunc = TypeVar("_InstrumentFunc", bound=Callable[..., Any])

    class _InstrumentTaskCallable(Protocol):
        def __call__(
            self, task_name: str, *, emit_metrics: bool = True
        ) -> Callable[[_InstrumentFunc], _InstrumentFunc]: ...

    instrument_task: _InstrumentTaskCallable = _instrument_task
else:
    instrument_task = _instrument_task

logger = structlog.get_logger(__name__)
_evaluate_alerts_sync: Callable[[], dict[str, int]] = async_to_sync(alerts_worker.evaluate_alert_rules)


async def _download_minio_async(uri: str) -> Path:
    from urllib.parse import urlparse

    parsed = urlparse(uri)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    session = aioboto3.Session()
    config = get_s3_client_config()
    tmpdir = Path(tempfile.mkdtemp(prefix="ingest_"))
    dst = tmpdir / Path(key).name
    async with session.client("s3", config=config, **get_s3_client_kwargs()) as client:
        response = await client.get_object(Bucket=bucket, Key=key)
        async with response["Body"] as body:
            with dst.open("wb") as handle:
                async for chunk in body.iter_chunks():
                    if chunk:
                        handle.write(chunk)
    return dst


def _download_minio_to_tmp(uri: str) -> Path:
    return asyncio.run(_download_minio_async(uri))


def _resolve_uri_to_path(uri: str) -> Path:
    if uri.startswith("minio://"):
        return _download_minio_to_tmp(uri)
    if uri.startswith("file://"):
        return Path(uri[len("file://") :])
    return Path(uri)


def _streaming_knobs() -> tuple[bool, int, int | None, int]:
    etl_cfg = getattr(settings, "etl", None)
    enabled = bool(etl_cfg.ingest_streaming_enabled if etl_cfg else getattr(settings, "INGEST_STREAMING_ENABLED", True))
    threshold_mb = int(
        etl_cfg.ingest_streaming_threshold_mb if etl_cfg else getattr(settings, "INGEST_STREAMING_THRESHOLD_MB", 50)
    )
    default_rows = 50_000
    chunk_rows_value = int(
        etl_cfg.ingest_streaming_chunk_size
        if etl_cfg
        else getattr(settings, "INGEST_STREAMING_CHUNK_SIZE", default_rows)
    )
    env_chunk_override = os.getenv("INGEST_STREAMING_CHUNK_SIZE")
    rows_override = False
    if env_chunk_override is not None:
        try:
            chunk_rows_value = int(env_chunk_override)
            rows_override = True
        except ValueError:
            rows_override = False
    if chunk_rows_value != default_rows:
        rows_override = True
    chunk_size = max(1, chunk_rows_value) if rows_override else None
    chunk_size_mb = int(
        etl_cfg.ingest_streaming_chunk_size_mb if etl_cfg else getattr(settings, "INGEST_STREAMING_CHUNK_SIZE_MB", 8)
    )
    return enabled, threshold_mb, chunk_size, chunk_size_mb


@celery_app.task(name="ingest.import_file", bind=True)  # type: ignore[misc]
@instrument_task("ingest.import_file", emit_metrics=False)
def task_import_file(
    self: Any,
    uri: str,
    report_type: str | None = None,
    force: bool = False,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Import a file into Postgres using existing ETL pipeline."""

    self.update_state(state=states.STARTED, meta={"stage": "resolve_uri"})
    tmp_dir: Path | None = None
    start_time = time.perf_counter()
    success = False
    try:
        local_path = _resolve_uri_to_path(uri)
        if "ingest_" in str(local_path.parent):
            tmp_dir = local_path.parent

        from etl import load_csv

        run_ingest = load_csv.import_file
        streaming_enabled, threshold_mb, chunk_size_rows, chunk_size_mb = _streaming_knobs()
        file_size_bytes = local_path.stat().st_size if local_path.exists() else None
        threshold_bytes = max(threshold_mb, 0) * 1024 * 1024
        streaming = bool(streaming_enabled and file_size_bytes is not None and file_size_bytes > threshold_bytes)
        chunk_rows = load_csv.resolve_streaming_chunk_rows(chunk_size=chunk_size_rows, chunk_size_mb=chunk_size_mb)

        self.update_state(state=states.STARTED, meta={"stage": "ingest"})
        record_ingest_task_mode("ingest.import_file", streaming=streaming, chunk_size_mb=chunk_size_mb)
        result = run_ingest(
            str(local_path),
            report_type=report_type,
            celery_update=lambda m: self.update_state(state=states.STARTED, meta=m),
            force=force,
            idempotency_key=idempotency_key,
            streaming=streaming,
            chunk_size=chunk_rows,
        )
        summary: dict[str, Any] = {}
        if isinstance(result, dict):
            summary.update(result)
        summary.setdefault("status", "success")
        summary.setdefault("streaming", streaming)
        summary.setdefault("streaming_chunk_rows", chunk_rows)
        summary.setdefault("streaming_chunk_size_mb", chunk_size_mb)
        self.update_state(state=states.SUCCESS, meta=summary)
        success = True
        return summary
    except Exception as exc:  # pragma: no cover - defensive
        task_id = getattr(getattr(self, "request", None), "id", None)
        logger.exception(
            "task_import_file.failed",
            task_id=task_id,
            uri=uri,
            report_type=report_type,
            error=str(exc),
        )
        meta = {"status": "error", "error": str(exc)}
        self.update_state(state=states.FAILURE, meta=meta)
        record_ingest_task_failure("ingest.import_file", exc)
        raise
    finally:
        record_ingest_task_outcome("ingest.import_file", success=success, duration_s=time.perf_counter() - start_time)
        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


@celery_app.task(name="ingest.rebuild_views", bind=True)  # type: ignore[misc]
@instrument_task("ingest.rebuild_views", emit_metrics=False)
def task_rebuild_views(self: Any) -> dict[str, Any]:
    logger.info("rebuild_views.noop")
    return {"status": "success", "message": "noop"}


if getattr(getattr(settings, "app", None), "testing", getattr(settings, "TESTING", False)):

    @celery_app.task(name="ingest.enqueue_import", bind=True)  # type: ignore[misc]
    def enqueue_import(self: Any, *, uri: str, dialect: str) -> dict[str, Any]:  # pragma: no cover - helper for tests
        from etl.load_csv import import_file as run_ingest

        return run_ingest(uri, dialect=dialect)


@celery_app.task(name="alertbot.run")  # type: ignore[misc]
@instrument_task("alertbot.run")
def alertbot_run() -> dict[str, Any]:
    """Periodic task that evaluates alert rules and dispatches notifications."""

    return _evaluate_alerts_sync()


def evaluate_alert_rules() -> dict[str, Any]:
    """Backward-compatible helper for legacy callers."""

    return _evaluate_alerts_sync()


@celery_app.task(name="alerts.rules_health")  # type: ignore[misc]
@instrument_task("alerts.rules_health")
def alert_rules_health_task() -> dict[str, Any]:
    """Celery task that reports Telegram/config health."""

    return alerts_worker.alert_rules_health()


def alert_rules_health() -> dict[str, Any]:
    """Return alert bot health without scheduling a dedicated Celery task."""

    return alerts_worker.alert_rules_health()
