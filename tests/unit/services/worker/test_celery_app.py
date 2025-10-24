import sys
from types import SimpleNamespace

import services.worker.celery_app as celery_module


def test_make_celery_configures_defaults(monkeypatch):
    monkeypatch.setattr(celery_module.settings, "REDIS_URL", "redis://cache/0")
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "true")
    app = celery_module.make_celery()
    assert app.conf.task_default_queue == "ingest"
    assert app.conf.task_always_eager is True


def test_init_sentry_if_dsn(monkeypatch):
    captured = {}

    def fake_init(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(celery_module.settings, "SENTRY_DSN", "https://dsn")

    stub_sentry = SimpleNamespace(init=fake_init)
    monkeypatch.setitem(sys.modules, "sentry_sdk", stub_sentry)
    monkeypatch.setitem(
        sys.modules,
        "sentry_sdk.integrations.celery",
        SimpleNamespace(CeleryIntegration=lambda: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "sentry_sdk.integrations.fastapi",
        SimpleNamespace(FastApiIntegration=lambda: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "sentry_sdk.integrations.sqlalchemy",
        SimpleNamespace(SqlalchemyIntegration=lambda: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "sentry_sdk.integrations.logging",
        SimpleNamespace(LoggingIntegration=lambda **kwargs: None),
    )
    celery_module._init_sentry()
    assert captured["dsn"] == "https://dsn"
