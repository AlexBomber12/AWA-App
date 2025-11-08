from awa_common import metrics
from awa_common.metrics import instrument_task


def test_textfile_contains_task_metrics(tmp_path, monkeypatch):
    monkeypatch.setattr(metrics.settings, "METRICS_TEXTFILE_DIR", str(tmp_path))
    monkeypatch.setattr(metrics.settings, "METRICS_FLUSH_INTERVAL_S", 0)
    metrics.init(service="worker_demo", env="test", version="1.2.3")
    metrics.TASK_RUNS_TOTAL.clear()
    metrics.TASK_DURATION_SECONDS.clear()
    metrics.TASK_ERRORS_TOTAL.clear()

    @instrument_task("worker_demo_task")
    def _task():
        return "ok"

    _task()
    prom_path = metrics.flush_textfile("worker_demo")
    assert prom_path.exists()
    content = prom_path.read_text()
    assert "task_runs_total" in content
