import pytest
from celery.schedules import crontab

from awa_common.cron_config import CronConfigError, CronSchedule, get_crontab, validate_cron_expr


def test_validate_cron_expr_returns_fields() -> None:
    fields = validate_cron_expr("0 2 * * *", source="NIGHTLY_MAINTENANCE_CRON")
    assert fields == ("0", "2", "*", "*", "*")


def test_validate_cron_expr_rejects_invalid() -> None:
    with pytest.raises(CronConfigError):
        validate_cron_expr("0 2 * *", source="BROKEN_CRON")


def test_cron_schedule_builds_celery_crontab() -> None:
    schedule = CronSchedule(name="TEST_CRON", expression="15 3 * * 1")
    crontab_obj = schedule.as_crontab()
    assert isinstance(crontab_obj, crontab)
    assert crontab_obj._orig_minute == "15"
    assert crontab_obj._orig_hour == "3"
    assert crontab_obj._orig_day_of_week == "1"


def test_get_crontab_matches_helper() -> None:
    schedule = get_crontab("*/10 * * * *", source="CHECK_INTERVAL")
    assert schedule._orig_minute == "*/10"
