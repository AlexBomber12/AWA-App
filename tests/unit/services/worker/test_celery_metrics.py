from collections.abc import Iterator

import pytest

from awa_common import metrics


def _monotonic(values: list[float]) -> Iterator[float]:
    yield from values


def _sample_value(family, labels: dict[str, str]) -> float:
    for sample in family.samples:
        if sample.labels == labels:
            return sample.value
    raise AssertionError(f"missing labels {labels}")


def test_celery_signal_handlers_record_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    metrics.init(service="worker", env="test", version="1.0.0")
    metrics.TASK_RUNS_TOTAL.clear()
    metrics.TASK_DURATION_SECONDS.clear()
    metrics.TASK_ERRORS_TOTAL.clear()
    metrics._TASK_START.clear()  # type: ignore[attr-defined]

    sequence = _monotonic([1.0, 2.0, 3.0, 4.5])
    monkeypatch.setattr(metrics.time, "perf_counter", lambda: next(sequence))

    class _FakeTask:
        name = "demo.task"

    metrics.on_task_prerun(sender=_FakeTask, task_id="success-1")
    metrics.on_task_postrun(sender=_FakeTask, task_id="success-1", state="SUCCESS")

    metrics.on_task_prerun(sender=_FakeTask, task_id="fail-1")
    metrics.on_task_failure(
        sender=_FakeTask,
        task_id="fail-1",
        exception=RuntimeError("boom"),
    )
    metrics.on_task_postrun(sender=_FakeTask, task_id="fail-1", state="FAILURE")

    labels_base = {"task": "demo.task", "service": "worker", "env": "test", "version": "1.0.0"}

    runs_family = metrics.TASK_RUNS_TOTAL.collect()[0]
    success_value = _sample_value(
        runs_family,
        {**labels_base, "status": "success"},
    )
    failure_value = _sample_value(
        runs_family,
        {**labels_base, "status": "failure"},
    )
    assert success_value == 1.0
    assert failure_value == 1.0

    failure_sample = metrics.TASK_ERRORS_TOTAL.collect()[0]
    assert _sample_value(failure_sample, {**labels_base, "error_type": "RuntimeError"}) == 1.0

    duration_family = metrics.TASK_DURATION_SECONDS.collect()[0]
    count = _sample_value(duration_family, {**labels_base, "le": "+Inf"})
    assert count == 2.0
