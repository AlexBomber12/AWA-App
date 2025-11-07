import types

from services.worker import healthcheck


def test_retry_success():
    calls = {"count": 0}

    def fn():
        calls["count"] += 1
        if calls["count"] < 2:
            raise RuntimeError("fail")

    assert healthcheck._retry(fn, attempts=3, delay=0) is True
    assert calls["count"] == 2


def test_retry_failure():
    def fn():
        raise RuntimeError("boom")

    assert healthcheck._retry(fn, attempts=1, delay=0, name="test") is False


def test_main_worker_role(monkeypatch):
    monkeypatch.setattr(healthcheck, "_retry", lambda fn, **kwargs: True)
    monkeypatch.setattr(healthcheck, "ping_worker", lambda: None)
    monkeypatch.setattr(healthcheck.celery_app, "conf", types.SimpleNamespace(beat_schedule={"job": 1}))
    exit_code = healthcheck.main(["worker"])
    assert exit_code == 0


def test_main_beat_missing_schedule(monkeypatch):
    monkeypatch.setattr(healthcheck, "_retry", lambda fn, **kwargs: True)
    monkeypatch.setattr(healthcheck.celery_app, "conf", types.SimpleNamespace(beat_schedule=None))
    exit_code = healthcheck.main(["beat"])
    assert exit_code == 1
