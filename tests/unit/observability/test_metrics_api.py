from awa_common import metrics


def test_http_client_metrics_samples(monkeypatch):
    metrics.init(service="api", env="test", version="1.0.0")
    metrics.HTTP_CLIENT_REQUESTS_TOTAL.clear()
    metrics.HTTP_CLIENT_REQUEST_DURATION_SECONDS.clear()

    metrics.record_http_client_request("keepa", "GET", 200, 0.2)
    metrics.record_http_client_request("keepa", "GET", None, 1.0)

    samples = metrics.HTTP_CLIENT_REQUESTS_TOTAL.collect()[0].samples
    assert any(sample.labels["status_class"] == "2xx" for sample in samples)
    assert any(sample.labels["status_class"] == "error" for sample in samples)

    durations = metrics.HTTP_CLIENT_REQUEST_DURATION_SECONDS.collect()[0].samples
    assert any(sample.value > 0 for sample in durations if sample.name.endswith("_sum"))
