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
    metrics.ETL_FAILURES_TOTAL.clear()
    metrics.ETL_LATENCY_SECONDS.clear()

    perf_values = iter([1.0, 2.0, 3.0, 4.2])
    monkeypatch.setattr(metrics.time, "perf_counter", lambda: next(perf_values))

    pipeline_labels = {"pipeline": "demo", "service": "worker", "env": "test", "version": "1.0.0"}

    with metrics.record_etl_run("demo"):
        pass

    with pytest.raises(RuntimeError):
        with metrics.record_etl_run("demo"):
            raise RuntimeError("boom")

    runs_family = metrics.ETL_RUNS_TOTAL.collect()[0]
    failures_family = metrics.ETL_FAILURES_TOTAL.collect()[0]
    latency_family = metrics.ETL_LATENCY_SECONDS.collect()[0]

    assert _sample_value(runs_family, pipeline_labels) == 2.0
    assert _sample_value(failures_family, pipeline_labels) == 1.0
    assert _sample_value(latency_family, {**pipeline_labels, "le": "+Inf"}) == 2.0
