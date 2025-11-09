import importlib
import sys
from types import SimpleNamespace

import pytest

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


def test_init_sentry_ignores_invalid_dsn(monkeypatch):
    import sentry_sdk
    from sentry_sdk.utils import BadDsn

    monkeypatch.setattr(celery_module.settings, "SENTRY_DSN", "https://dsn.example/1")

    def boom(*_args, **_kwargs):
        raise BadDsn("missing")

    monkeypatch.setattr(sentry_sdk, "init", boom)
    celery_module._init_sentry()  # should not raise


@pytest.fixture
def reload_celery_module():
    yield importlib.reload
    importlib.reload(celery_module)


def test_mv_refresh_schedule_enabled(monkeypatch, reload_celery_module):
    monkeypatch.setenv("SCHEDULE_NIGHTLY_MAINTENANCE", "false")
    monkeypatch.setenv("SCHEDULE_MV_REFRESH", "true")
    monkeypatch.setenv("MV_REFRESH_CRON", "*/15 * * * *")

    module = reload_celery_module(celery_module)
    schedule = module.celery_app.conf.beat_schedule
    entry = schedule.get("refresh-roi-fees-mvs")
    assert entry is not None
    cron = entry["schedule"]
    assert cron._orig_minute == "*/15"
    assert cron._orig_hour == "*"
    assert cron._orig_day_of_week == "*"


def test_mv_refresh_schedule_invalid_cron_falls_back(monkeypatch, reload_celery_module):
    monkeypatch.setenv("SCHEDULE_NIGHTLY_MAINTENANCE", "false")
    monkeypatch.setenv("SCHEDULE_MV_REFRESH", "true")
    monkeypatch.setenv("MV_REFRESH_CRON", "bad")

    module = reload_celery_module(celery_module)
    schedule = module.celery_app.conf.beat_schedule
    entry = schedule.get("refresh-roi-fees-mvs")
    assert entry is not None
    cron = entry["schedule"]
    assert cron._orig_minute == "*/15"
    assert cron._orig_hour == "*"
    assert cron._orig_day_of_week == "*"


def test_mv_refresh_schedule_disabled(monkeypatch, reload_celery_module):
    monkeypatch.setenv("SCHEDULE_NIGHTLY_MAINTENANCE", "false")
    monkeypatch.setenv("SCHEDULE_MV_REFRESH", "false")

    module = reload_celery_module(celery_module)
    schedule = module.celery_app.conf.beat_schedule
    assert "refresh-roi-fees-mvs" not in schedule


def test_mv_refresh_and_nightly_merge_and_handle_import_error(monkeypatch, reload_celery_module):
    monkeypatch.setenv("SCHEDULE_NIGHTLY_MAINTENANCE", "true")
    monkeypatch.setenv("NIGHTLY_MAINTENANCE_CRON", "bad")
    monkeypatch.setenv("SCHEDULE_MV_REFRESH", "true")
    monkeypatch.setenv("MV_REFRESH_CRON", "*/10 * * * *")

    calls = []
    original_import = celery_module.importlib.import_module
    triggered = False

    def fake_import(name, *args, **kwargs):
        nonlocal triggered
        if name == "services.worker.tasks" and not triggered:
            calls.append(name)
            triggered = True
            raise RuntimeError("boom")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(celery_module.importlib, "import_module", fake_import, raising=False)

    module = reload_celery_module(celery_module)
    schedule = module.celery_app.conf.beat_schedule
    assert {"nightly-maintenance", "refresh-roi-fees-mvs"}.issubset(set(schedule.keys()))

    nightly = schedule["nightly-maintenance"]["schedule"]
    assert nightly._orig_minute == "30"
    assert nightly._orig_hour == "2"

    refresh = schedule["refresh-roi-fees-mvs"]["schedule"]
    assert refresh._orig_minute == "*/10"

    assert calls == ["services.worker.tasks"]


def test_alerts_schedule_uses_legacy_env(monkeypatch, reload_celery_module):
    monkeypatch.setenv("CHECK_INTERVAL_MIN", "10")
    module = reload_celery_module(celery_module)
    schedule = module.celery_app.conf.beat_schedule
    entry = schedule["alerts-evaluate-rules"]
    cron = entry["schedule"]
    assert cron._orig_minute == "*/10"
    assert "alerts-telegram-health" in schedule
