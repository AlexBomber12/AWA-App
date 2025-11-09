from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

import structlog

from awa_common.metrics import (
    ALERTS_NOTIFICATIONS_FAILED_TOTAL,
    ALERTS_RULE_DURATION_SECONDS,
    ALERTS_RULE_EVALUATIONS_TOTAL,
)
from awa_common.settings import settings
from awa_common.telegram import send_message, validate_config

from . import rules as db_rules
from .rules_store import SUPPORTED_RULE_KEYS, DbRulesStore, FileRulesStore, RuleConfig, RulesStore

ChannelName = str
RuleRunner = Callable[[dict[str, Any]], Awaitable["RuleEvaluation"]]
R = TypeVar("R", bound=RuleRunner)

_SERVICE = settings.SERVICE_NAME or "worker"
_ENV = settings.ENV
_VERSION = settings.VERSION
_CHANNEL = "telegram"
_logger = structlog.get_logger(__name__).bind(service=_SERVICE, env=_ENV, version=_VERSION, component="alerts")


@dataclass(slots=True)
class RuleEvaluation:
    events: int
    messages: list[str]


@dataclass(frozen=True, slots=True)
class RuleHandler:
    key: str
    runner: RuleRunner


_RULE_HANDLERS: dict[str, RuleHandler] = {}


def _register_handler(key: str) -> Callable[[R], R]:
    def decorator(func: R) -> R:
        _RULE_HANDLERS[key] = RuleHandler(key=key, runner=func)
        return func

    return decorator


def _metric_labels(rule: str, **extra: str) -> dict[str, str]:
    labels = {
        "rule": rule,
        "service": _SERVICE,
        "env": _ENV,
        "version": _VERSION,
    }
    labels.update(extra)
    return labels


def _notification_labels(rule: str, error_type: str) -> dict[str, str]:
    return {
        "rule": rule,
        "channel": _CHANNEL,
        "error_type": error_type,
        "service": _SERVICE,
        "env": _ENV,
        "version": _VERSION,
    }


def _rule_duration_labels(rule: str) -> dict[str, str]:
    return {
        "rule": rule,
        "service": _SERVICE,
        "env": _ENV,
        "version": _VERSION,
    }


def _build_store() -> RulesStore:
    source = (settings.ALERT_RULES_SOURCE or "yaml").strip().lower()
    if source == "yaml":
        path = settings.ALERT_RULES_FILE or "config/alert_rules.yaml"
        return FileRulesStore(Path(path))
    if source == "db":
        return DbRulesStore()
    _logger.warning("alerts.rules.unsupported_source", source=source, fallback="yaml")
    return FileRulesStore(Path(settings.ALERT_RULES_FILE or "config/alert_rules.yaml"))


RULES_STORE: RulesStore = _build_store()
TELEGRAM_ENABLED: bool = False
_TELEGRAM_REASON: str = "not validated"
_LAST_TELEGRAM_STATE: bool | None = None


def revalidate_telegram(*, force_log: bool = False) -> tuple[bool, str]:
    """Recompute the Telegram availability flag and log when it changes."""

    global TELEGRAM_ENABLED, _TELEGRAM_REASON, _LAST_TELEGRAM_STATE
    token = settings.TELEGRAM_TOKEN
    chat_id = settings.TELEGRAM_DEFAULT_CHAT_ID
    TELEGRAM_ENABLED, _TELEGRAM_REASON = validate_config(token, chat_id)
    if force_log or _LAST_TELEGRAM_STATE != TELEGRAM_ENABLED:
        if TELEGRAM_ENABLED:
            _logger.info("alerts.telegram.enabled", reason=_TELEGRAM_REASON)
        else:
            _logger.warning(
                "alerts.telegram.disabled",
                message=f"Telegram disabled: {_TELEGRAM_REASON}",
                reason=_TELEGRAM_REASON,
            )
    _LAST_TELEGRAM_STATE = TELEGRAM_ENABLED
    return TELEGRAM_ENABLED, _TELEGRAM_REASON


revalidate_telegram(force_log=True)


async def evaluate_alert_rules(now: datetime | None = None) -> dict[str, int]:
    """Evaluate alert rules and dispatch notifications."""

    if not settings.ALERTS_ENABLED:
        _logger.info("alerts.disabled", reason="ALERTS_ENABLED=0")
        return {"rules_total": 0, "triggered": 0, "notifications_sent": 0, "notifications_failed": 0}

    rules = _load_rules()
    current_time = now or datetime.now(UTC)
    summary = {"rules_total": len(rules), "triggered": 0, "notifications_sent": 0, "notifications_failed": 0}

    for rule in rules:
        handler = _RULE_HANDLERS.get(rule.key)
        if handler is None:
            _logger.warning("alerts.rule.unsupported", rule=rule.key)
            continue
        result_label = "skipped"
        start = time.perf_counter()
        try:
            if not rule.enabled:
                _logger.info("alerts.rule.skip", rule=rule.key, reason="disabled")
                continue
            if rule.schedule_cron and not _cron_matches(rule.schedule_cron, current_time):
                _logger.debug("alerts.rule.skip", rule=rule.key, reason="schedule_mismatch", cron=rule.schedule_cron)
                continue
            evaluation = await handler.runner(rule.thresholds)
            if evaluation.events <= 0:
                _logger.debug("alerts.rule.skip", rule=rule.key, reason="no_events")
                continue
            result_label = "triggered"
            summary["triggered"] += 1
            await _dispatch_notifications(rule, evaluation, summary)
        except Exception as exc:  # pragma: no cover - defensive logging around DB access
            result_label = "error"
            _logger.exception("alerts.rule.error", rule=rule.key, error=str(exc))
        finally:
            duration = time.perf_counter() - start
            ALERTS_RULE_DURATION_SECONDS.labels(**_rule_duration_labels(rule.key)).observe(duration)
            ALERTS_RULE_EVALUATIONS_TOTAL.labels(**_metric_labels(rule.key, result=result_label)).inc()
    return summary


def _load_rules() -> list[RuleConfig]:
    try:
        return RULES_STORE.list_rules()
    except FileNotFoundError as exc:
        _logger.warning("alerts.rules.file_missing", path=str(exc))
    except NotImplementedError as exc:
        _logger.warning("alerts.rules.store_unimplemented", source=settings.ALERT_RULES_SOURCE, error=str(exc))
    except ValueError as exc:
        _logger.error("alerts.rules.invalid", error=str(exc))
    return _default_rules()


def _default_rules() -> list[RuleConfig]:
    return [RuleConfig(key=key, enabled=True, channels={"telegram": True}) for key in sorted(SUPPORTED_RULE_KEYS)]


async def _dispatch_notifications(rule: RuleConfig, evaluation: RuleEvaluation, summary: dict[str, int]) -> None:
    message_count = len(evaluation.messages) or 1
    if not rule.channel_enabled(_CHANNEL):
        _logger.info("alerts.rule.channel_disabled", rule=rule.key, channel=_CHANNEL)
        ALERTS_NOTIFICATIONS_FAILED_TOTAL.labels(**_notification_labels(rule.key, "disabled")).inc(message_count)
        summary["notifications_failed"] += message_count
        return
    if not TELEGRAM_ENABLED:
        _logger.warning("alerts.rule.telegram_disabled", rule=rule.key, reason=_TELEGRAM_REASON)
        ALERTS_NOTIFICATIONS_FAILED_TOTAL.labels(**_notification_labels(rule.key, "disabled")).inc(message_count)
        summary["notifications_failed"] += message_count
        return
    sent = 0
    failed = 0
    for message in evaluation.messages:
        success = await send_message(message, rule=rule.key)
        if success:
            sent += 1
        else:
            failed += 1
    if sent:
        summary["notifications_sent"] += sent
    if failed:
        summary["notifications_failed"] += failed


def alert_rules_health() -> dict[str, Any]:
    """Revalidate Telegram configuration for observability."""

    enabled, reason = revalidate_telegram(force_log=False)
    return {"telegram_enabled": enabled, "reason": reason}


def _cron_matches(expr: str, when: datetime) -> bool:
    fields = expr.strip().split()
    if len(fields) != 5:
        return False
    minute, hour, day, month, weekday = fields
    return (
        _cron_field_matches(minute, when.minute, 0, 59)
        and _cron_field_matches(hour, when.hour, 0, 23)
        and _cron_field_matches(day, when.day, 1, 31)
        and _cron_field_matches(month, when.month, 1, 12)
        and _cron_field_matches(weekday, when.weekday(), 0, 6)
    )


def _cron_field_matches(field: str, value: int, minimum: int, maximum: int) -> bool:
    field = field.strip()
    if field == "*":
        return True
    result = False
    for part in field.split(","):
        part = part.strip()
        if not part:
            continue
        if part.startswith("*/"):
            step = _coerce_int(part[2:], 1)
            if step <= 0:
                continue
            if (value - minimum) % step == 0:
                result = True
                break
        elif "-" in part:
            bounds = part.split("-", 1)
            start = _coerce_int(bounds[0], minimum)
            end = _coerce_int(bounds[1], maximum)
            if start <= value <= end:
                result = True
                break
        else:
            if value == _coerce_int(part, value + 1):
                result = True
                break
    return result


def _coerce_int(candidate: Any, default: int) -> int:
    try:
        return int(candidate)
    except (TypeError, ValueError):
        return default


def _threshold_int(thresholds: dict[str, Any], key: str, default: int) -> int:
    return _coerce_int(thresholds.get(key), default)


def _threshold_float(thresholds: dict[str, Any], key: str, default: float) -> float:
    try:
        raw = thresholds.get(key, default)
        value = float(raw)
        return value
    except (TypeError, ValueError):
        return float(default)


def _format_number(value: Any) -> str:
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not value.is_integer():
            return f"{value:.2f}"
        return str(int(value))
    return str(value)


@_register_handler("roi")
async def _run_roi(thresholds: dict[str, Any]) -> RuleEvaluation:
    min_roi = _threshold_float(thresholds, "min_roi", settings.ROI_THRESHOLD)
    min_days = _threshold_int(thresholds, "min_days", settings.ROI_DURATION_DAYS)
    rows = await db_rules.query_roi_breaches(min_roi, min_days)
    if not rows:
        return RuleEvaluation(events=0, messages=[])
    lines = [f"{row['asin']} {_format_number(row['roi_pct'])}%" for row in rows]
    title = f"⚠️ Маржа по товару упала ниже {_format_number(min_roi)} %. Проверьте цену и закупочную стоимость."
    return RuleEvaluation(events=len(rows), messages=[f"{title}\n" + "\n".join(lines)])


@_register_handler("price_increase_pct")
async def _run_price_increase(thresholds: dict[str, Any]) -> RuleEvaluation:
    grow_pct = _threshold_float(thresholds, "grow_pct", settings.COST_DELTA_PCT)
    rows = await db_rules.query_price_increase(grow_pct)
    if not rows:
        return RuleEvaluation(events=0, messages=[])
    lines = [f"{row['sku']} {_format_number(row['delta'])}%" for row in rows]
    title = f"💸 Закупочная цена выросла > {_format_number(grow_pct)}%"
    body = "\n".join(lines) + "\n👉 Свяжитесь с поставщиком или ищите альтернативу."
    return RuleEvaluation(events=len(rows), messages=[f"{title}\n{body}"])


@_register_handler("buybox_drop_pct")
async def _run_buybox_drop(thresholds: dict[str, Any]) -> RuleEvaluation:
    drop_pct = _threshold_float(thresholds, "drop_pct", settings.PRICE_DROP_PCT)
    rows = await db_rules.query_buybox_drop(drop_pct)
    if not rows:
        return RuleEvaluation(events=0, messages=[])
    lines = [f"{row['asin']} {_format_number(row['drop_pct'])}%" for row in rows]
    title = f"🏷️ Цена Buy Box упала > {_format_number(drop_pct)}% за 48 ч"
    body = "\n".join(lines) + "\n👉 Решите: снизить цену или распродать остатки."
    return RuleEvaluation(events=len(rows), messages=[f"{title}\n{body}"])


@_register_handler("returns_rate_pct")
async def _run_returns(thresholds: dict[str, Any]) -> RuleEvaluation:
    returns_pct = _threshold_float(thresholds, "returns_pct", settings.RETURNS_PCT)
    rows = await db_rules.query_high_returns(returns_pct)
    if not rows:
        return RuleEvaluation(events=0, messages=[])
    lines = [f"{row['asin']} {_format_number(row['returns_ratio'])}%" for row in rows]
    title = f"🔄 Доля возвратов > {_format_number(returns_pct)}% за 30 дней"
    body = "\n".join(lines) + "\n👉 Проверьте качество товара и описание листинга."
    return RuleEvaluation(events=len(rows), messages=[f"{title}\n{body}"])


@_register_handler("stale_price_days")
async def _run_stale_price_lists(thresholds: dict[str, Any]) -> RuleEvaluation:
    stale_days = _threshold_int(thresholds, "stale_days", settings.STALE_DAYS)
    rows = await db_rules.query_stale_price_lists(stale_days)
    if not rows:
        return RuleEvaluation(events=0, messages=[])
    lines = [f"vendor {row['vendor_id']}" for row in rows]
    title = f"📜 Прайс-лист устарел > {stale_days} дней"
    body = "\n".join(lines) + "\n👉 Запросите свежий прайс у поставщика."
    return RuleEvaluation(events=len(rows), messages=[f"{title}\n{body}"])


__all__ = ["evaluate_alert_rules", "alert_rules_health", "revalidate_telegram", "TELEGRAM_ENABLED"]
