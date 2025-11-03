from collections.abc import Iterator

import pytest

from services.worker import metrics


def _sample_value(metric, sample_name: str, labels: dict[str, str]) -> float:
    family = metric.collect()[0]
    candidates = {sample_name}
    if sample_name.endswith("_total"):
        candidates.add(sample_name[: -len("_total")])
    for sample in family.samples:
        if sample.labels == labels and sample.name in candidates:
            return sample.value
    raise AssertionError(f"missing sample {sample_name} with labels {labels}")


def _monotonic_sequence(values: list[float]) -> Iterator[float]:
    yield from values


def test_metrics_signals_increment_and_time(monkeypatch: pytest.MonkeyPatch) -> None:
    metrics.celery_task_started_total.clear()
    metrics.celery_task_succeeded_total.clear()
    metrics.celery_task_failed_total.clear()
    metrics.celery_task_duration_seconds.clear()
    metrics._start_times.clear()  # type: ignore[attr-defined]

    # Deterministic monotonic clock to assert the histogram observation.
    monotonic_iter = _monotonic_sequence([1.0, 2.4])
    monkeypatch.setattr(metrics.time, "monotonic", lambda: next(monotonic_iter))

    class _FakeTask:
        name = "logistics.test"

    task_id = "abc123"
    metrics._on_task_prerun(sender=_FakeTask, task_id=task_id)
    metrics._on_task_postrun(
        sender=_FakeTask,
        task_id=task_id,
        state="SUCCESS",
    )
    metrics._on_task_failure(sender=_FakeTask, task_id="xyz789")

    labels = {"task": "logistics.test"}

    assert (
        _sample_value(metrics.celery_task_started_total, "celery_task_started_total_total", labels)
        == 1.0
    )
    assert (
        _sample_value(
            metrics.celery_task_succeeded_total,
            "celery_task_succeeded_total_total",
            labels,
        )
        == 1.0
    )
    assert (
        _sample_value(metrics.celery_task_failed_total, "celery_task_failed_total_total", labels)
        == 1.0
    )
    assert metrics._start_times == {}  # type: ignore[attr-defined]

    # Histogram exports _count and _sum samples for the labelset.
    count = _sample_value(
        metrics.celery_task_duration_seconds,
        "celery_task_duration_seconds_count",
        labels,
    )
    total = _sample_value(
        metrics.celery_task_duration_seconds,
        "celery_task_duration_seconds_sum",
        labels,
    )
    assert count == 1.0
    assert total == pytest.approx(1.4, rel=1e-6)
