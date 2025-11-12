from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast

import structlog

from awa_common.metrics import (
    ALERTBOT_BATCH_DURATION_SECONDS,
    ALERTBOT_EVENTS_EMITTED_TOTAL,
    ALERTBOT_RULE_EVAL_DURATION_SECONDS,
    ALERTBOT_RULES_EVALUATED_TOTAL,
    ALERTBOT_STARTUP_VALIDATION_OK,
)
from awa_common.settings import settings
from awa_common.telegram import AsyncTelegramClient
from services.alert_bot import config as config_module
from services.alert_bot.config import AlertRule, AlertRulesRuntime
from services.alert_bot.rules import AlertEvent, evaluate_rule
from services.alert_bot.rules_store import SUPPORTED_RULE_KEYS, DbRulesStore, FileRulesStore, RuleConfig, RulesStore

logger = structlog.get_logger(__name__).bind(
    service=settings.SERVICE_NAME or "alert_bot",
    env=settings.ENV,
    version=settings.VERSION,
    component="alert_bot",
)

_METRIC_LABELS = {
    "service": (settings.SERVICE_NAME or "alert_bot") or "alert_bot",
    "env": settings.ENV or "local",
    "version": settings.VERSION,
}
ALERTBOT_STARTUP_VALIDATION_OK.labels(**_METRIC_LABELS).set(0)


@dataclass(slots=True)
class RuleEvaluationResult:
    rule: AlertRule
    events: list[AlertEvent]
    outcome: str
    duration: float


@dataclass(slots=True)
class BatchStats:
    rules_total: int = 0
    rules_evaluated: int = 0
    events_total: int = 0
    messages_planned: int = 0
    messages_sent: int = 0
    messages_failed: int = 0
    retries: int = 0
    send_latencies: list[float] = field(default_factory=list)
    degraded: bool = False
    degraded_reason: str | None = None


class RuleScheduler:
    """Track per-rule schedules (cron expressions or @every intervals)."""

    def __init__(self) -> None:
        self._last_every_run: dict[str, datetime] = {}
        self._every_intervals: dict[str, float] = {}

    def due_rules(self, rules: Iterable[AlertRule], *, now: datetime) -> list[AlertRule]:
        due: list[AlertRule] = []
        for rule in rules:
            if not rule.enabled:
                continue
            schedule = (rule.schedule or "").strip()
            if not schedule:
                due.append(rule)
                continue
            if schedule.startswith("@every"):
                interval = self._parse_every(rule.id, schedule)
                last_run = self._last_every_run.get(rule.id)
                if last_run is None or (now - last_run).total_seconds() >= interval:
                    due.append(rule)
                    self._last_every_run[rule.id] = now
                continue
            if _cron_matches(schedule, now):
                due.append(rule)
        return due

    def _parse_every(self, rule_id: str, schedule: str) -> float:
        cached = self._every_intervals.get(rule_id)
        if cached:
            return cached
        expr = schedule[len("@every") :].strip()
        if not expr:
            interval = 60.0
        else:
            number = ""
            unit = ""
            for ch in expr:
                if ch.isdigit():
                    number += ch
                else:
                    unit = (expr[len(number) :]).strip().lower()
                    break
            try:
                value = float(number or "60")
            except ValueError:
                value = 60.0
            multiplier = _INTERVAL_MULTIPLIERS.get(unit or "s") or 60.0
            interval = max(value * multiplier, 1.0)
        self._every_intervals[rule_id] = interval
        return interval


_INTERVAL_MULTIPLIERS = {
    "s": 1.0,
    "sec": 1.0,
    "secs": 1.0,
    "second": 1.0,
    "seconds": 1.0,
    "m": 60.0,
    "min": 60.0,
    "mins": 60.0,
    "minute": 60.0,
    "minutes": 60.0,
    "h": 3600.0,
    "hour": 3600.0,
    "hours": 3600.0,
}


class AlertBotRunner:
    def __init__(self) -> None:
        self._client = AsyncTelegramClient()
        self._config_manager = config_module.CONFIG_MANAGER
        self._legacy_store: RulesStore = _build_legacy_store()
        self._scheduler = RuleScheduler()
        self._send_semaphore = asyncio.Semaphore(max(1, settings.ALERT_SEND_CONCURRENCY))
        self._max_retries = 3
        self._sending_enabled = False
        self._last_validation_version: str | None = None
        self._last_validated_chat_ids: frozenset[str] = frozenset()
        self._degraded_reason: str | None = "validation_not_run"

    async def run(self, now: datetime | None = None) -> dict[str, Any]:
        if not settings.ALERTS_ENABLED:
            logger.info("alertbot.disabled", reason="ALERTS_ENABLED=0")
            return {
                "rules_total": 0,
                "notifications_sent": 0,
                "notifications_failed": 0,
                "events_emitted": 0,
                "degraded": False,
            }
        batch_start = time.perf_counter()
        stats = BatchStats()
        runtime_config = self._load_config()
        rules, source = self._resolve_rules(runtime_config)
        stats.rules_total = len(rules)
        if not rules:
            logger.warning("alertbot.no_rules", source=source)
            return _format_summary(stats, duration=time.perf_counter() - batch_start)

        now = now or datetime.now(UTC)
        due_rules = self._scheduler.due_rules(rules, now=now)
        if not due_rules:
            logger.debug("alertbot.no_due_rules", total=len(rules))
            return _format_summary(stats, duration=time.perf_counter() - batch_start)

        events = await self._evaluate_rules(due_rules, stats)
        deduped_events = _dedupe_events(events)
        stats.events_total = len(deduped_events)
        await self._ensure_validation(runtime_config, deduped_events)
        stats.degraded = not self._sending_enabled
        stats.degraded_reason = self._degraded_reason
        await self._dispatch_events(deduped_events, stats)

        batch_duration = time.perf_counter() - batch_start
        ALERTBOT_BATCH_DURATION_SECONDS.labels(**_METRIC_LABELS).observe(batch_duration)

        p95_ms = _percentile(stats.send_latencies, 95.0) * 1000 if stats.send_latencies else 0.0
        logger.info(
            "alertbot.batch_complete",
            rules_total=stats.rules_total,
            due_rules=len(due_rules),
            events=stats.events_total,
            messages_sent=stats.messages_sent,
            messages_failed=stats.messages_failed,
            retries=stats.retries,
            duration_s=round(batch_duration, 3),
            p95_send_ms=int(p95_ms),
            degraded=stats.degraded,
            reason=stats.degraded_reason,
            source=source,
        )
        return _format_summary(stats, duration=batch_duration)

    def health(self) -> dict[str, Any]:
        return {
            "sending_enabled": self._sending_enabled,
            "reason": self._degraded_reason,
        }

    async def validate_startup(self) -> None:
        runtime_config = self._load_config()
        rules, _ = self._resolve_rules(runtime_config)
        placeholder_events = [
            AlertEvent(
                rule_id=rule.id,
                chat_ids=rule.chat_ids,
                text="startup-validation",
                dedupe_key=f"{rule.id}:startup",
                parse_mode=rule.parse_mode,
            )
            for rule in rules
        ]
        await self._ensure_validation(runtime_config, placeholder_events)

    def _load_config(self) -> AlertRulesRuntime | None:
        runtime = self._config_manager.get()
        if runtime is None:
            runtime = self._config_manager.load(force=True)
        else:
            updated = self._config_manager.maybe_reload()
            if updated is not None:
                runtime = updated
        return runtime

    def _resolve_rules(self, runtime: AlertRulesRuntime | None) -> tuple[list[AlertRule], str]:
        if runtime:
            return runtime.enabled_rules(), "config"
        legacy_rules = self._legacy_rules()
        if legacy_rules:
            return legacy_rules, "legacy"
        fallback_rules = self._default_rules()
        return fallback_rules, "default"

    async def _evaluate_rules(self, rules: list[AlertRule], stats: BatchStats) -> list[AlertEvent]:
        concurrency = max(1, settings.ALERT_EVAL_CONCURRENCY)
        semaphore = asyncio.Semaphore(concurrency)
        tasks = [self._evaluate_single_rule(rule, semaphore) for rule in rules]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        events: list[AlertEvent] = []
        for result in results:
            if isinstance(result, RuleEvaluationResult):
                stats.rules_evaluated += 1
                events.extend(result.events)
            elif isinstance(result, Exception):
                logger.exception("alertbot.rule.evaluate_error", error=str(result))
        return events

    async def _evaluate_single_rule(self, rule: AlertRule, semaphore: asyncio.Semaphore) -> RuleEvaluationResult:
        start = time.perf_counter()
        outcome = "ok"
        events: list[AlertEvent] = []
        async with semaphore:
            try:
                events = await asyncio.wait_for(evaluate_rule(rule), timeout=settings.ALERT_RULE_TIMEOUT_S)
            except TimeoutError:
                outcome = "timeout"
                logger.warning("alertbot.rule.timeout", rule_id=rule.id, timeout_s=settings.ALERT_RULE_TIMEOUT_S)
            except Exception as exc:  # pragma: no cover - defensive logging
                outcome = "error"
                logger.exception("alertbot.rule.error", rule_id=rule.id, error=str(exc))
        duration = time.perf_counter() - start
        ALERTBOT_RULE_EVAL_DURATION_SECONDS.labels(rule=rule.id, **_METRIC_LABELS).observe(duration)
        ALERTBOT_RULES_EVALUATED_TOTAL.labels(rule=rule.id, outcome=outcome, **_METRIC_LABELS).inc()
        if events:
            ALERTBOT_EVENTS_EMITTED_TOTAL.labels(rule=rule.id, **_METRIC_LABELS).inc(len(events))
        return RuleEvaluationResult(rule=rule, events=events, outcome=outcome, duration=duration)

    async def _ensure_validation(self, runtime: AlertRulesRuntime | None, events: list[AlertEvent]) -> None:
        if not events:
            return
        config_version = runtime.version if runtime else "legacy"
        chat_ids = frozenset(_collect_chat_ids(runtime, events))
        needs_validation = (
            not self._sending_enabled
            or self._last_validation_version != config_version
            or chat_ids != self._last_validated_chat_ids
        )
        if not needs_validation:
            return
        await self._run_validation(chat_ids, config_version)

    async def _run_validation(self, chat_ids: frozenset[str], config_version: str) -> None:
        if not chat_ids:
            self._set_degraded("no_chat_ids_configured")
            return
        token_status = await self._client.get_me()
        if not token_status.ok:
            self._set_degraded(token_status.description or "invalid_token")
            return
        for chat_id in chat_ids:
            chat_status = await self._client.get_chat(chat_id)
            if not chat_status.ok:
                description = chat_status.description or "unknown_error"
                logger.error("alertbot.validation.chat_failed", chat_id=chat_id, error=description)
                self._set_degraded(f"chat_invalid:{chat_id}")
                return
        self._sending_enabled = True
        self._degraded_reason = None
        self._last_validation_version = config_version
        self._last_validated_chat_ids = chat_ids
        ALERTBOT_STARTUP_VALIDATION_OK.labels(**_METRIC_LABELS).set(1)
        logger.info("alertbot.validation.success", chats=len(chat_ids))

    async def _dispatch_events(self, events: list[AlertEvent], stats: BatchStats) -> None:
        if not events:
            return
        if not self._sending_enabled:
            skipped = sum(len(event.chat_ids) for event in events)
            stats.messages_failed += skipped
            logger.warning("alertbot.sending_skipped", reason=self._degraded_reason, messages=skipped)
            return
        send_tasks: list[asyncio.Task[None]] = []
        for event in events:
            for chat_id in event.chat_ids:
                stats.messages_planned += 1
                send_tasks.append(asyncio.create_task(self._send_event(chat_id, event, stats)))
        if send_tasks:
            await asyncio.gather(*send_tasks)

    async def _send_event(self, chat_id: str, event: AlertEvent, stats: BatchStats) -> None:
        attempt = 0
        while attempt < self._max_retries:
            attempt += 1
            async with self._send_semaphore:
                send_start = time.perf_counter()
                result = await self._client.send_message(
                    chat_id=chat_id,
                    text=event.text,
                    parse_mode=event.parse_mode,
                    disable_web_page_preview=event.disable_web_page_preview,
                    rule_id=event.rule_id,
                )
                stats.send_latencies.append(time.perf_counter() - send_start)
            if result.ok:
                stats.messages_sent += 1
                return
            if result.status == "retry":
                stats.retries += 1
                await asyncio.sleep(max(result.retry_after or 1.0, 0.1))
                continue
            stats.messages_failed += 1
            return
        stats.messages_failed += 1

    def _set_degraded(self, reason: str) -> None:
        self._sending_enabled = False
        self._degraded_reason = reason
        ALERTBOT_STARTUP_VALIDATION_OK.labels(**_METRIC_LABELS).set(0)
        logger.error("alertbot.validation.failed", reason=reason)

    def _legacy_rules(self) -> list[AlertRule]:
        try:
            legacy_configs = self._legacy_store.list_rules()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("alertbot.legacy_rules.error", error=str(exc))
            return []
        return _convert_legacy_rules(legacy_configs)

    def _default_rules(self) -> list[AlertRule]:
        configs = [
            RuleConfig(key=key, enabled=True, thresholds={}, channels={"telegram": True})
            for key in sorted(SUPPORTED_RULE_KEYS)
        ]
        return _convert_legacy_rules(configs)


def _collect_chat_ids(runtime: AlertRulesRuntime | None, events: list[AlertEvent]) -> set[str]:
    chats: set[str] = set()
    if runtime is not None:
        chats.update(runtime.chat_ids())
    if events:
        for event in events:
            chats.update(event.chat_ids)
    if chats:
        return chats
    default_chat = settings.TELEGRAM_DEFAULT_CHAT_ID
    if default_chat is None:
        return set()
    return {str(default_chat)}


def _build_legacy_store() -> RulesStore:
    source = (settings.ALERT_RULES_SOURCE or "yaml").strip().lower()
    if source == "yaml":
        path = settings.ALERT_RULES_FILE or "config/alert_rules.yaml"
        return FileRulesStore(path)
    if source == "db":
        return DbRulesStore()
    logger.warning("alertbot.legacy.unsupported_source", source=source, fallback="yaml")
    return FileRulesStore(settings.ALERT_RULES_FILE or "config/alert_rules.yaml")


LEGACY_RULE_TYPE_MAP = {
    "roi": "roi_drop",
    "price_increase_pct": "price_increase_pct",
    "buybox_drop_pct": "buybox_loss",
    "returns_rate_pct": "returns_spike",
    "stale_price_days": "price_outdated",
}


def _convert_legacy_rules(configs: list[RuleConfig]) -> list[AlertRule]:
    chat_default = settings.TELEGRAM_DEFAULT_CHAT_ID
    chat_ids = [str(chat_default)] if chat_default is not None else []
    converted: list[AlertRule] = []
    for config in configs:
        if not config.enabled or not config.channel_enabled("telegram"):
            continue
        mapped_type = LEGACY_RULE_TYPE_MAP.get(config.key)
        if not mapped_type:
            continue
        rule_type = cast(config_module.RuleType, mapped_type)
        params = _legacy_params(config.key, config.thresholds)
        if config.thresholds.get("chat_id"):
            target = config.thresholds["chat_id"]
            chats = [str(target)]
        else:
            chats = list(chat_ids)
        if not chats:
            logger.warning("alertbot.legacy_rule.no_chat", rule=config.key)
            continue
        converted.append(
            AlertRule(
                id=config.key,
                type=rule_type,
                enabled=True,
                schedule=config.schedule_cron,
                chat_ids=chats,
                parse_mode="HTML",
                params=params,
                template=None,
            )
        )
    return converted


def _legacy_params(rule_key: str, thresholds: dict[str, Any]) -> dict[str, Any]:
    params = dict(thresholds)
    if rule_key == "roi":
        if "min_roi_pct" not in params and "min_roi" in params:
            params["min_roi_pct"] = params.pop("min_roi")
        params.setdefault("min_roi_pct", settings.ROI_THRESHOLD)
        params.setdefault("min_days", settings.ROI_DURATION_DAYS)
    if rule_key == "price_increase_pct":
        params.setdefault("grow_pct", settings.COST_DELTA_PCT)
    if rule_key == "buybox_drop_pct":
        params.setdefault("drop_pct", settings.PRICE_DROP_PCT)
    if rule_key == "returns_rate_pct":
        params.setdefault("returns_pct", settings.RETURNS_PCT)
    if rule_key == "stale_price_days":
        params.setdefault("stale_days", settings.STALE_DAYS)
    return params


def _dedupe_events(events: Iterable[AlertEvent]) -> list[AlertEvent]:
    seen: OrderedDict[str, AlertEvent] = OrderedDict()
    for event in events:
        if event.dedupe_key in seen:
            continue
        seen[event.dedupe_key] = event
    return list(seen.values())


def _percentile(samples: list[float], percentile: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    rank = (percentile / 100.0) * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _format_summary(stats: BatchStats, *, duration: float) -> dict[str, Any]:
    summary = {
        "rules_total": stats.rules_total,
        "rules_evaluated": stats.rules_evaluated,
        "events_emitted": stats.events_total,
        "notifications_sent": stats.messages_sent,
        "notifications_failed": stats.messages_failed,
        "messages_planned": stats.messages_planned,
        "retries": stats.retries,
        "duration_s": round(duration, 3),
        "degraded": stats.degraded,
        "degraded_reason": stats.degraded_reason,
    }
    return summary


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
    for part in field.split(","):
        part = part.strip()
        if not part:
            continue
        if part.startswith("*/"):
            step = _safe_int(part[2:], 1)
            if step > 0 and (value - minimum) % step == 0:
                return True
        elif "-" in part:
            start, _, end = part.partition("-")
            start_int = _safe_int(start, minimum)
            end_int = _safe_int(end, maximum)
            if start_int <= value <= end_int:
                return True
        else:
            if value == _safe_int(part, value + 1):
                return True
    return False


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


RUNNER = AlertBotRunner()


async def evaluate_alert_rules(now: datetime | None = None) -> dict[str, Any]:
    return await RUNNER.run(now=now)


def alert_rules_health() -> dict[str, Any]:
    return RUNNER.health()


def run_startup_validation() -> None:
    """Synchronously trigger startup validation for Celery worker processes."""

    try:
        asyncio.run(RUNNER.validate_startup())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(RUNNER.validate_startup())
        finally:
            loop.close()


__all__ = ["evaluate_alert_rules", "alert_rules_health", "run_startup_validation"]
