import pytest

from awa_common import metrics


def _sample_value(family, labels: dict[str, str]) -> float:
    for sample in family.samples:
        if sample.labels == labels:
            return sample.value
    raise AssertionError(f"missing labels {labels}")


def test_record_etl_run_tracks_success_and_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    metrics.init(service="worker", env="test", version="1.0.0")
    metrics.ETL_RUNS_TOTAL.clear()
    metrics.ETL_RETRY_TOTAL.clear()
    metrics.ETL_DURATION_SECONDS.clear()

    perf_values = iter([1.0, 2.0, 3.0, 4.2])
    monkeypatch.setattr(metrics.time, "perf_counter", lambda: next(perf_values))

    run_labels = {"job": "demo", "service": "worker", "env": "test", "version": "1.0.0"}

    with metrics.record_etl_run("demo"):
        pass

    with pytest.raises(RuntimeError):
        with metrics.record_etl_run("demo"):
            raise RuntimeError("boom")

    runs_family = metrics.ETL_RUNS_TOTAL.collect()[0]
    duration_family = metrics.ETL_DURATION_SECONDS.collect()[0]
    retries_family = metrics.ETL_RETRY_TOTAL.collect()[0]

    assert _sample_value(runs_family, run_labels) == 2.0
    assert _sample_value(retries_family, {**run_labels, "reason": "exception"}) == 1.0
    assert _sample_value(duration_family, {**run_labels, "le": "+Inf"}) == 2.0
