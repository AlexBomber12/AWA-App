from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from croniter import croniter
from croniter.croniter import CroniterBadCronError
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from celery.schedules import crontab as CrontabSchedule

__all__ = [
    "CronConfigError",
    "CronSchedule",
    "get_crontab",
    "validate_cron_expr",
]


class CronConfigError(ValueError):
    """Raised when a cron expression fails validation."""


def _format_source(source: str | None) -> str:
    return source or "cron expression"


def validate_cron_expr(cron_expr: str, *, source: str | None = None) -> tuple[str, str, str, str, str]:
    """Validate a cron expression using croniter and return its component fields."""
    normalized = (cron_expr or "").strip()
    label = _format_source(source)
    if not normalized:
        raise CronConfigError(f"{label} must be set.")
    try:
        croniter(normalized)
    except CroniterBadCronError as exc:  # pragma: no cover - exercised via calling sites
        raise CronConfigError(f"{label} {normalized!r} is invalid: {exc}") from exc
    parts = normalized.split()
    if len(parts) != 5:
        raise CronConfigError(f"{label} {normalized!r} must contain 5 fields.")
    minute, hour, day_of_month, month_of_year, day_of_week = parts
    return (
        str(minute),
        str(hour),
        str(day_of_month),
        str(month_of_year),
        str(day_of_week),
    )


def get_crontab(cron_expr: str, *, source: str | None = None) -> CrontabSchedule:
    """Return a Celery crontab schedule for the validated expression."""
    from celery.schedules import crontab as celery_crontab

    minute, hour, day_of_month, month_of_year, day_of_week = validate_cron_expr(cron_expr, source=source)
    return celery_crontab(
        minute=minute,
        hour=hour,
        day_of_month=day_of_month,
        month_of_year=month_of_year,
        day_of_week=day_of_week,
    )


@dataclass(frozen=True)
class CronFields:
    minute: str
    hour: str
    day_of_month: str
    month_of_year: str
    day_of_week: str


class CronSchedule(BaseModel):
    """Typed cron configuration that validates itself and exposes Celery schedules."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(description="Setting or logical name tied to the cron expression.")
    expression: str = Field(description="Raw cron expression.")

    _fields: CronFields | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _validate_expression(self) -> CronSchedule:
        minute, hour, day_of_month, month_of_year, day_of_week = validate_cron_expr(self.expression, source=self.name)
        self._fields = CronFields(
            minute=minute,
            hour=hour,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
            day_of_week=day_of_week,
        )
        return self

    def as_crontab(self) -> CrontabSchedule:
        """Return a Celery crontab using the validated expression."""
        from celery.schedules import crontab as celery_crontab

        if self._fields is None:
            minute, hour, day_of_month, month_of_year, day_of_week = validate_cron_expr(
                self.expression, source=self.name
            )
            self._fields = CronFields(
                minute=minute,
                hour=hour,
                day_of_month=day_of_month,
                month_of_year=month_of_year,
                day_of_week=day_of_week,
            )
        return celery_crontab(
            minute=self._fields.minute,
            hour=self._fields.hour,
            day_of_month=self._fields.day_of_month,
            month_of_year=self._fields.month_of_year,
            day_of_week=self._fields.day_of_week,
        )
