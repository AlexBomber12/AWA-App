from __future__ import annotations

from packages.awa_common import metrics as m


def _base_labels(**extra: str) -> dict[str, str]:
    labels = dict(m._BASE_LABEL_VALUES)
    labels.update(extra)
    return labels


def _metric_value(metric, **labels) -> float:
    metric.labels(**labels)  # ensure child exists
    for collected in metric.collect():
        for sample in collected.samples:
            if sample.labels == labels:
                return sample.value
    return 0.0


def test_record_ingest_upload_and_failure_metrics() -> None:
    labels = _base_labels(extension="csv")
    before = _metric_value(m.AWA_INGEST_UPLOAD_BYTES_TOTAL, **labels)
    m.record_ingest_upload(25, 0.5, extension="csv")
    after = _metric_value(m.AWA_INGEST_UPLOAD_BYTES_TOTAL, **labels)
    assert after == before + 25

    fail_labels = _base_labels(extension="csv", reason="413")
    before_fail = _metric_value(m.AWA_INGEST_UPLOAD_FAILURES_TOTAL, **fail_labels)
    m.record_ingest_upload_failure(extension="csv", reason="413")
    assert _metric_value(m.AWA_INGEST_UPLOAD_FAILURES_TOTAL, **fail_labels) == before_fail + 1


def test_record_ingest_download_metrics() -> None:
    labels = _base_labels(scheme="http")
    before = _metric_value(m.AWA_INGEST_DOWNLOAD_BYTES_TOTAL, **labels)
    m.record_ingest_download(50, 1.0, scheme="http")
    assert _metric_value(m.AWA_INGEST_DOWNLOAD_BYTES_TOTAL, **labels) == before + 50

    fail_labels = _base_labels(scheme="http", reason="timeout")
    before_fail = _metric_value(m.AWA_INGEST_DOWNLOAD_FAILURES_TOTAL, **fail_labels)
    m.record_ingest_download_failure(scheme="http", reason="timeout")
    assert _metric_value(m.AWA_INGEST_DOWNLOAD_FAILURES_TOTAL, **fail_labels) == before_fail + 1
