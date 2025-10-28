from __future__ import annotations

import os
import threading
import time
from typing import Any

from celery import signals
from prometheus_client import Counter, Histogram, start_http_server

celery_task_started_total = Counter(
    "celery_task_started_total",
    "tasks started",
    ("task",),
)
celery_task_succeeded_total = Counter(
    "celery_task_succeeded_total",
    "tasks succeeded",
    ("task",),
)
celery_task_failed_total = Counter(
    "celery_task_failed_total",
    "tasks failed",
    ("task",),
)
celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "task duration",
    ("task",),
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 30),
)

_start_times: dict[str, float] = {}
_lock = threading.Lock()
_server_lock = threading.Lock()
_METRICS_SERVER_STARTED = False


def _task_label(sender: Any) -> str:
    name = getattr(sender, "name", None)
    if isinstance(name, str):
        return name
    if isinstance(sender, str):
        return sender
    cls = getattr(sender, "__class__", None)
    cls_name = getattr(cls, "__name__", None)
    if isinstance(cls_name, str):
        return cls_name
    return "unknown"


def _on_task_prerun(sender: Any, task_id: str, **_kwargs: Any) -> None:
    label = _task_label(sender)
    celery_task_started_total.labels(task=label).inc()
    if not task_id:
        return
    with _lock:
        _start_times[task_id] = time.monotonic()


def _on_task_postrun(
    sender: Any,
    task_id: str,
    retval: Any | None = None,
    **kwargs: Any,
) -> None:
    label = _task_label(sender)
    state = kwargs.get("state")
    if state == "SUCCESS":
        celery_task_succeeded_total.labels(task=label).inc()
    start_time = None
    if task_id:
        with _lock:
            start_time = _start_times.pop(task_id, None)
    if start_time is not None:
        duration = time.monotonic() - start_time
        celery_task_duration_seconds.labels(task=label).observe(duration)


def _on_task_failure(
    sender: Any,
    task_id: str,
    exception: BaseException | None = None,
    **_kwargs: Any,
) -> None:
    label = _task_label(sender)
    celery_task_failed_total.labels(task=label).inc()


signals.task_prerun.connect(_on_task_prerun, weak=False)
signals.task_postrun.connect(_on_task_postrun, weak=False)
signals.task_failure.connect(_on_task_failure, weak=False)


def maybe_start_metrics_server(port: int) -> None:
    global _METRICS_SERVER_STARTED
    with _server_lock:
        if _METRICS_SERVER_STARTED:
            return
        if os.getenv("TESTING", "0") == "1":
            return
        start_http_server(port)
        _METRICS_SERVER_STARTED = True


__all__ = [
    "celery_task_duration_seconds",
    "celery_task_failed_total",
    "celery_task_started_total",
    "celery_task_succeeded_total",
    "maybe_start_metrics_server",
]
