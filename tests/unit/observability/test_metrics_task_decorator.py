import pytest

from awa_common import metrics
from awa_common.metrics import instrument_task


def _reset_metrics():
    metrics.TASK_RUNS_TOTAL.clear()
    metrics.TASK_DURATION_SECONDS.clear()
    metrics.TASK_ERRORS_TOTAL.clear()


def test_instrument_task_success(monkeypatch):
    metrics.init(service="worker", env="test", version="1")
    _reset_metrics()

    @instrument_task("demo_task")
    def _task():
        return "ok"

    assert _task() == "ok"
    runs = metrics.TASK_RUNS_TOTAL.collect()[0].samples
    assert any(sample.labels["status"] == "success" for sample in runs)


def test_instrument_task_error(monkeypatch):
    metrics.init(service="worker", env="test", version="1")
    _reset_metrics()

    @instrument_task("demo_task")
    def _failing():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        _failing()

    runs = metrics.TASK_RUNS_TOTAL.collect()[0].samples
    assert any(sample.labels["status"] == "error" for sample in runs)
    errors = metrics.TASK_ERRORS_TOTAL.collect()[0].samples
    assert any(sample.labels["error_type"] == "RuntimeError" for sample in errors)
