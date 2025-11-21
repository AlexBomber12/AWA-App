from __future__ import annotations

import asyncio
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast

import structlog
from croniter import croniter as croniter_cls

from awa_common.cron_config import CronConfigError, validate_cron_expr
from awa_common.metrics import (
    ALERT_ERRORS_TOTAL,
    ALERT_RULE_SKIPPED_TOTAL,
    ALERTBOT_BATCH_DURATION_SECONDS,
    ALERTBOT_EVENTS_EMITTED_TOTAL,
    ALERTBOT_RULE_EVAL_DURATION_SECONDS,
    ALERTBOT_RULES_EVALUATED_TOTAL,
    ALERTBOT_RULES_SUPPRESSED_TOTAL,
    ALERTBOT_STARTUP_VALIDATION_OK,
)
from awa_common.settings import settings
from services.alert_bot import config as config_module
from services.alert_bot.config import AlertRule, AlertRulesRuntime
from services.alert_bot.decider import AlertRequest, RuleDecision, build_alert_requests
from services.alert_bot.rules import AlertEvent, evaluate_rule
from services.alert_bot.rules_store import SUPPORTED_RULE_KEYS, DbRulesStore, FileRulesStore, RuleConfig, RulesStore
from services.alert_bot.settings import AlertBotSettings
from services.alert_bot.transport import TelegramTransport

_DEFAULT_ALERT_SETTINGS = AlertBotSettings.load()

logger = structlog.get_logger(__name__).bind(
    service=_DEFAULT_ALERT_SETTINGS.service_name,
    env=_DEFAULT_ALERT_SETTINGS.env,
    version=_DEFAULT_ALERT_SETTINGS.version,
    component="alert_bot",
)

_METRIC_LABELS = _DEFAULT_ALERT_SETTINGS.base_metric_labels()
ALERTBOT_STARTUP_VALIDATION_OK.labels(**_METRIC_LABELS).set(0)


class AlertConfigurationError(Exception):
    """Raised when alert bot configuration is invalid."""


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
        self._validated_cron: set[str] = set()
        self._invalid_cron: set[str] = set()

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
            if self._cron_due(rule.id, schedule, now):
                due.append(rule)
        return due

    def _cron_due(self, rule_id: str, schedule: str, now: datetime) -> bool:
        expression = schedule.strip()
        if not expression:
            return True
        if expression not in self._validated_cron:
            if expression in self._invalid_cron:
                return False
            try:
                validate_cron_expr(expression, source=f"rule:{rule_id}")
            except CronConfigError as exc:
                if expression not in self._invalid_cron:
                    logger.warning("alertbot.invalid_rule_cron", rule=rule_id, cron=expression, error=str(exc))
                    self._invalid_cron.add(expression)
                return False
            self._validated_cron.add(expression)
        try:
            return bool(croniter_cls.match(expression, now))
        except Exception as exc:
            logger.warning("alertbot.cron_match_failed", rule=rule_id, cron=expression, error=str(exc))
            self._validated_cron.discard(expression)
            self._invalid_cron.add(expression)
            return False

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
    def __init__(self, *, settings: AlertBotSettings | None = None, transport: TelegramTransport | None = None) -> None:
        self._settings = settings or AlertBotSettings.load()
        self._metric_labels = self._settings.base_metric_labels()
        self._transport = transport or TelegramTransport(metric_labels=self._metric_labels)
        self._config_manager = config_module.CONFIG_MANAGER
        self._legacy_store: RulesStore = _build_legacy_store()
        self._scheduler = RuleScheduler()
        self._send_semaphore = asyncio.Semaphore(max(1, self._settings.send_concurrency))
        self._max_retries = 3
        self._sending_enabled = False
        self._last_validation_version: str | None = None
        self._last_validated_chat_ids: frozenset[str] = frozenset()
        self._degraded_reason: str | None = "validation_not_run"

    async def run(self, now: datetime | None = None) -> dict[str, Any]:
        if not self._settings.enabled:
            logger.info("alertbot.disabled", reason="ALERTS_ENABLED=0")
            self._record_rule_skip("global", "disabled")
            return {
                "rules_total": 0,
                "notifications_sent": 0,
                "notifications_failed": 0,
                "events_emitted": 0,
                "degraded": False,
            }
        settings_ok, config_reason = self._settings.validate_runtime()
        if not settings_ok:
            self._record_config_error("global")
            self._raise_config_error(config_reason or "invalid_config")
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
        skipped_ids = {rule.id for rule in rules} - {rule.id for rule in due_rules}
        for rule_id in skipped_ids:
            self._record_rule_skip(rule_id, "filtered")
        if not due_rules:
            logger.debug("alertbot.no_due_rules", total=len(rules))
            return _format_summary(stats, duration=time.perf_counter() - batch_start)

        evaluations = await self._evaluate_rules(due_rules, stats)
        decisions = [RuleDecision(rule=result.rule, events=result.events) for result in evaluations if result.events]
        requests = build_alert_requests(decisions)
        stats.events_total = len(requests)
        await self._ensure_validation(runtime_config, requests)
        stats.degraded = not self._sending_enabled
        stats.degraded_reason = self._degraded_reason
        await self._dispatch_requests(requests, stats)

        batch_duration = time.perf_counter() - batch_start
        ALERTBOT_BATCH_DURATION_SECONDS.labels(**self._metric_labels).observe(batch_duration)

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
        if not self._settings.enabled:
            logger.info("alertbot.disabled", reason="ALERTS_ENABLED=0")
            return
        ok, reason = self._settings.validate_runtime()
        if not ok:
            self._record_config_error("global")
            self._raise_config_error(reason or "invalid_config")
        runtime_config = self._load_config()
        rules, _ = self._resolve_rules(runtime_config)
        placeholder_requests: list[AlertRequest] = []
        for rule in rules:
            severity = str(rule.params.get("severity", "info")) if isinstance(rule.params, dict) else "info"
            for chat_id in rule.chat_ids:
                placeholder_requests.append(
                    AlertRequest(
                        rule_id=rule.id,
                        severity=severity,
                        chat_id=str(chat_id),
                        message="startup-validation",
                        parse_mode=rule.parse_mode,
                        dedupe_key=f"{rule.id}:startup:{chat_id}",
                        disable_web_page_preview=True,
                        labels={},
                    )
                )
        await self._ensure_validation(runtime_config, placeholder_requests, fail_fast=True)

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

    async def _evaluate_rules(self, rules: list[AlertRule], stats: BatchStats) -> list[RuleEvaluationResult]:
        concurrency = max(1, self._settings.eval_concurrency)
        semaphore = asyncio.Semaphore(concurrency)
        tasks = [self._evaluate_single_rule(rule, semaphore) for rule in rules]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        evaluations: list[RuleEvaluationResult] = []
        for result in results:
            if isinstance(result, RuleEvaluationResult):
                stats.rules_evaluated += 1
                evaluations.append(result)
            elif isinstance(result, Exception):
                logger.exception("alertbot.rule.evaluate_error", error=str(result))
        return evaluations

    async def _evaluate_single_rule(self, rule: AlertRule, semaphore: asyncio.Semaphore) -> RuleEvaluationResult:
        start = time.perf_counter()
        outcome = "ok"
        events: list[AlertEvent] = []
        async with semaphore:
            try:
                events = await asyncio.wait_for(evaluate_rule(rule), timeout=self._settings.rule_timeout_s)
            except TimeoutError:
                outcome = "timeout"
                logger.warning("alertbot.rule.timeout", rule_id=rule.id, timeout_s=self._settings.rule_timeout_s)
            except Exception as exc:  # pragma: no cover - defensive logging
                outcome = "error"
                logger.exception("alertbot.rule.error", rule_id=rule.id, error=str(exc))
        duration = time.perf_counter() - start
        ALERTBOT_RULE_EVAL_DURATION_SECONDS.labels(rule=rule.id, **self._metric_labels).observe(duration)
        ALERTBOT_RULES_EVALUATED_TOTAL.labels(rule=rule.id, outcome=outcome, **self._metric_labels).inc()
        if events:
            ALERTBOT_EVENTS_EMITTED_TOTAL.labels(rule=rule.id, **self._metric_labels).inc(len(events))
        return RuleEvaluationResult(rule=rule, events=events, outcome=outcome, duration=duration)

    async def _ensure_validation(
        self, runtime: AlertRulesRuntime | None, requests: list[AlertRequest], *, fail_fast: bool = False
    ) -> None:
        if not requests:
            return
        config_version = runtime.version if runtime else "legacy"
        chat_ids = frozenset(_collect_chat_ids(runtime, requests, self._settings))
        needs_validation = (
            not self._sending_enabled
            or self._last_validation_version != config_version
            or chat_ids != self._last_validated_chat_ids
        )
        if not needs_validation:
            return
        await self._run_validation(chat_ids, config_version, fail_fast=fail_fast)

    async def _run_validation(self, chat_ids: frozenset[str], config_version: str, *, fail_fast: bool = False) -> None:
        if not chat_ids:
            reason = "no_chat_ids_configured"
            self._record_config_error("global")
            if fail_fast:
                self._raise_config_error(reason)
            self._set_degraded(reason)
            return
        ok_config, reason_config = self._settings.validate_runtime()
        reason_text = reason_config or "invalid_config"
        if not ok_config:
            self._record_config_error("global")
            if fail_fast:
                self._raise_config_error(reason_text)
            self._set_degraded(reason_text)
            return
        ok_transport, reason_transport = await self._transport.validate(set(chat_ids))
        validation_reason = reason_transport or "validation_failed"
        if not ok_transport:
            self._record_config_error("global")
            if fail_fast:
                self._raise_config_error(validation_reason)
            self._set_degraded(validation_reason)
            return
        self._sending_enabled = True
        self._degraded_reason = None
        self._last_validation_version = config_version
        self._last_validated_chat_ids = chat_ids
        ALERTBOT_STARTUP_VALIDATION_OK.labels(**self._metric_labels).set(1)
        logger.info("alertbot.validation.success", chats=len(chat_ids))

    async def _dispatch_requests(self, requests: list[AlertRequest], stats: BatchStats) -> None:
        if not requests:
            return
        if not self._sending_enabled:
            skipped = len(requests)
            stats.messages_failed += skipped
            for request in requests:
                self._record_rule_skip(request.rule_id, "disabled")
            logger.warning("alertbot.sending_skipped", reason=self._degraded_reason, messages=skipped)
            return
        send_tasks: list[asyncio.Task[None]] = []
        for request in requests:
            stats.messages_planned += 1
            send_tasks.append(asyncio.create_task(self._send_request(request, stats)))
        if send_tasks:
            await asyncio.gather(*send_tasks)

    async def _send_request(self, request: AlertRequest, stats: BatchStats) -> None:
        attempt = 0
        while attempt < self._max_retries:
            attempt += 1
            async with self._send_semaphore:
                send_start = time.perf_counter()
                result = await self._transport.send(request)
                stats.send_latencies.append(time.perf_counter() - send_start)
            if result.ok:
                stats.messages_sent += 1
                return
            if result.status == "retry":
                stats.retries += 1
                await asyncio.sleep(max(result.retry_after or 1.0, 0.1))
                continue
            stats.messages_failed += 1
            logger.error(
                "alertbot.send.failed",
                rule_id=request.rule_id,
                chat_id=request.chat_id,
                status=result.status,
                error_type=result.error_type,
                description=result.description,
            )
            return
        stats.messages_failed += 1

    def _raise_config_error(self, reason: str) -> None:
        message = (reason or "invalid_config").strip() or "invalid_config"
        fix_hint = "Set TELEGRAM_TOKEN and TELEGRAM_DEFAULT_CHAT_ID to valid values"
        self._set_degraded(message, fix=fix_hint, exit_code=1)
        raise AlertConfigurationError(message)

    def _set_degraded(self, reason: str, *, fix: str | None = None, exit_code: int | None = None) -> None:
        self._sending_enabled = False
        self._degraded_reason = reason
        ALERTBOT_STARTUP_VALIDATION_OK.labels(**self._metric_labels).set(0)
        logger.error("alertbot.validation.failed", reason=reason, fix=fix, exit_code=exit_code)

    def _record_config_error(self, rule_id: str) -> None:
        ALERT_ERRORS_TOTAL.labels(rule=rule_id, type="config_error", **self._metric_labels).inc()

    def _record_rule_skip(self, rule_id: str, reason: str) -> None:
        ALERT_RULE_SKIPPED_TOTAL.labels(rule=rule_id, reason=reason, **self._metric_labels).inc()
        ALERTBOT_RULES_SUPPRESSED_TOTAL.labels(rule=rule_id, reason=reason, **self._metric_labels).inc()

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


def _collect_chat_ids(
    runtime: AlertRulesRuntime | None,
    requests: list[AlertRequest],
    bot_settings: AlertBotSettings,
) -> set[str]:
    chats: set[str] = set()
    if runtime is not None:
        chats.update(runtime.chat_ids())
    if requests:
        for request in requests:
            chats.add(request.chat_id)
    if chats:
        return chats
    default_chat = bot_settings.default_chat_id
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


RUNNER = AlertBotRunner()


async def evaluate_alert_rules(now: datetime | None = None) -> dict[str, Any]:
    return await RUNNER.run(now=now)


def alert_rules_health() -> dict[str, Any]:
    return RUNNER.health()


def run_startup_validation() -> None:
    """Synchronously trigger startup validation for Celery worker processes."""

    try:
        try:
            asyncio.run(RUNNER.validate_startup())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(RUNNER.validate_startup())
            finally:
                loop.close()
    except AlertConfigurationError as exc:
        raise SystemExit(f"Alert bot configuration invalid: {exc}") from exc


__all__ = ["AlertConfigurationError", "evaluate_alert_rules", "alert_rules_health", "run_startup_validation"]
