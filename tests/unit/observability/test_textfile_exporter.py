from awa_common import metrics


def test_flush_textfile(tmp_path, monkeypatch):
    monkeypatch.setattr(metrics.settings, "METRICS_TEXTFILE_DIR", str(tmp_path))
    monkeypatch.setattr(metrics.settings, "METRICS_FLUSH_INTERVAL_S", 0)
    metrics.init(service="metrics_demo", env="test", version="1")
    path = metrics.flush_textfile("metrics_demo")
    assert path == tmp_path / "awa_metrics_demo.prom"
    assert path.exists()
    assert path.read_text().strip()
