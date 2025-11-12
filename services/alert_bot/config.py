from __future__ import annotations

import importlib
import signal
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from types import FrameType
from typing import Any, Literal, get_args

import structlog
from pydantic import BaseModel, Field, field_validator, model_validator

from awa_common.settings import settings

yaml = importlib.import_module("yaml")
RuleType = Literal[
    "roi_drop",
    "buybox_loss",
    "returns_spike",
    "price_outdated",
    "custom",
    "roi",
    "price_increase_pct",
    "buybox_drop_pct",
    "returns_rate_pct",
    "stale_price_days",
]

_SUPPORTED_RULE_TYPES = set(get_args(RuleType))

_LOGGER = structlog.get_logger(__name__).bind(
    service=settings.SERVICE_NAME or "worker",
    env=settings.ENV,
    version=settings.VERSION,
    component="alert_rules_config",
)


def _normalize_rule_id(value: str) -> str:
    text = (value or "").strip().lower()
    if not text:
        raise ValueError("rule id must be a non-empty string")
    return text


def _coerce_chat_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        chats = [str(item).strip() for item in value]
    else:
        chats = [str(value).strip()]
    return [chat for chat in chats if chat]


class RuleDefaults(BaseModel):
    enabled: bool = True
    parse_mode: str | None = "HTML"
    chat_id: list[str] = Field(default_factory=list, alias="chat_id")

    @field_validator("chat_id", mode="before")
    @classmethod
    def _coerce_chat_ids(cls, value: Any) -> list[str]:
        return _coerce_chat_list(value)


class RuleEntry(BaseModel):
    id: str
    type: RuleType
    enabled: bool | None = None
    schedule: str | None = None
    chat_id: list[str] | None = Field(default=None, alias="chat_id")
    parse_mode: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    template: str | None = None

    @field_validator("id", mode="before")
    @classmethod
    def _normalize_id(cls, value: Any) -> str:
        return _normalize_rule_id(str(value))

    @field_validator("type", mode="before")
    @classmethod
    def _normalize_type(cls, value: Any) -> str:
        text = (value or "").strip().lower()
        if text not in _SUPPORTED_RULE_TYPES:
            raise ValueError(f"Unsupported rule type: {value!r}")
        return text

    @field_validator("schedule", mode="before")
    @classmethod
    def _normalize_schedule(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("chat_id", mode="before")
    @classmethod
    def _coerce_chat_ids(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        return _coerce_chat_list(value)


class AlertRulesDocument(BaseModel):
    version: str | int = 1
    defaults: RuleDefaults = Field(default_factory=RuleDefaults)
    rules: list[RuleEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_rules(self) -> AlertRulesDocument:
        seen: set[str] = set()
        for rule in self.rules:
            if rule.id in seen:
                raise ValueError(f"Duplicate rule id: {rule.id}")
            seen.add(rule.id)
        return self

    def to_runtime(self, path: Path, overrides: dict[str, bool]) -> AlertRulesRuntime:
        defaults = AlertRuleDefaults(
            enabled=self.defaults.enabled,
            parse_mode=self.defaults.parse_mode,
            chat_ids=list(self.defaults.chat_id),
        )
        resolved_rules: list[AlertRule] = []
        for entry in self.rules:
            chat_ids = list(entry.chat_id) if entry.chat_id is not None else list(defaults.chat_ids)
            if not chat_ids:
                raise ValueError(f"rule '{entry.id}' does not define chat_id and defaults.chat_id is empty")
            enabled = entry.enabled if entry.enabled is not None else defaults.enabled
            override = overrides.get(entry.id)
            if override is not None:
                enabled = override
            resolved_rules.append(
                AlertRule(
                    id=entry.id,
                    type=entry.type,
                    enabled=bool(enabled),
                    schedule=entry.schedule,
                    chat_ids=chat_ids,
                    parse_mode=entry.parse_mode or defaults.parse_mode,
                    params=dict(entry.params),
                    template=entry.template,
                )
            )
        return AlertRulesRuntime(
            version=str(self.version),
            defaults=defaults,
            rules=resolved_rules,
            source_path=path,
            loaded_at=time.time(),
        )


@dataclass(slots=True)
class AlertRuleDefaults:
    enabled: bool
    parse_mode: str | None
    chat_ids: list[str]


@dataclass(slots=True)
class AlertRule:
    id: str
    type: RuleType
    enabled: bool
    schedule: str | None
    chat_ids: list[str]
    parse_mode: str | None
    params: dict[str, Any]
    template: str | None


@dataclass(slots=True)
class AlertRulesRuntime:
    version: str
    defaults: AlertRuleDefaults
    rules: list[AlertRule]
    source_path: Path
    loaded_at: float

    def enabled_rules(self) -> list[AlertRule]:
        return [rule for rule in self.rules if rule.enabled]

    def chat_ids(self) -> set[str]:
        ids: set[str] = set()
        for rule in self.rules:
            if not rule.enabled:
                continue
            ids.update(rule.chat_ids)
        return ids


def parse_rule_overrides(value: str | None) -> dict[str, bool]:
    if not value:
        return {}
    overrides: dict[str, bool] = {}
    for part in value.split(","):
        chunk = part.strip()
        if not chunk:
            continue
        name, sep, status = chunk.partition(":")
        if not sep:
            continue
        rule_id = _normalize_rule_id(name)
        normalized_status = status.strip().lower()
        if normalized_status in {"1", "true", "yes", "on", "enable", "enabled"}:
            overrides[rule_id] = True
        elif normalized_status in {"0", "false", "no", "off", "disable", "disabled"}:
            overrides[rule_id] = False
    return overrides


def load_config(path: str | Path, *, overrides: dict[str, bool] | None = None) -> AlertRulesRuntime:
    config_path = Path(path)
    text = config_path.read_text(encoding="utf-8")
    raw = yaml.safe_load(text) or {}
    if not isinstance(raw, dict):
        raise ValueError("alert bot config must be a mapping at the root level")
    document = AlertRulesDocument.model_validate(raw)
    override_map = overrides or {}
    return document.to_runtime(config_path, override_map)


_ACTIVE_MANAGER: AlertConfigManager | None = None


def _handle_sighup(signum: int, _frame: FrameType | None) -> None:  # pragma: no cover - exercised via integration
    if signum != signal.SIGHUP:
        return
    manager = _ACTIVE_MANAGER
    if manager is not None:
        manager.request_reload()


class AlertConfigManager:
    """Manage loading and reloading of alert bot rule configuration."""

    _signal_installed = False
    _signal_lock = threading.Lock()

    def __init__(
        self,
        path: str | Path | None = None,
        *,
        watch: bool | None = None,
        watch_interval: float | None = None,
        overrides: dict[str, bool] | None = None,
    ) -> None:
        self._path = Path(path or settings.ALERT_RULES_PATH)
        self._watch_enabled = bool(settings.ALERT_RULES_WATCH if watch is None else watch)
        self._watch_interval = watch_interval if watch_interval is not None else settings.ALERT_RULES_WATCH_INTERVAL_S
        self._lock = threading.Lock()
        self._config: AlertRulesRuntime | None = None
        self._mtime_ns: int | None = None
        self._last_checked: float = 0.0
        self._pending_reload = False
        self._overrides = overrides if overrides is not None else parse_rule_overrides(settings.ALERT_RULES_OVERRIDE)
        self._logger = _LOGGER.bind(config_path=str(self._path))
        self._install_signal_handler()

    def _install_signal_handler(self) -> None:
        global _ACTIVE_MANAGER
        _ACTIVE_MANAGER = self
        if AlertConfigManager._signal_installed:
            return
        with AlertConfigManager._signal_lock:
            if AlertConfigManager._signal_installed:
                return
            try:  # pragma: no cover - depends on runtime environment
                signal.signal(signal.SIGHUP, _handle_sighup)
                AlertConfigManager._signal_installed = True
            except (AttributeError, ValueError):
                # Windows or threads without signal support; skip.
                self._logger.debug("alert_rules_config.signal_unsupported")

    def request_reload(self) -> None:
        self._pending_reload = True

    def get(self) -> AlertRulesRuntime | None:
        return self._config

    def load(self, *, force: bool = False) -> AlertRulesRuntime | None:
        with self._lock:
            return self._load(force=force)

    def maybe_reload(self, *, force: bool = False) -> AlertRulesRuntime | None:
        with self._lock:
            if force or self._pending_reload:
                self._pending_reload = False
                return self._load(force=True)
            if not self._watch_enabled:
                return self._config
            now = time.monotonic()
            if self._last_checked and now - self._last_checked < max(self._watch_interval, 1.0):
                return self._config
            self._last_checked = now
            return self._load(force=False)

    def _load(self, *, force: bool) -> AlertRulesRuntime | None:
        try:
            current_mtime = self._path.stat().st_mtime_ns
        except FileNotFoundError:
            self._logger.warning("alert_rules_config.file_missing", path=str(self._path))
            self._config = None
            self._mtime_ns = None
            return None
        if not force and self._config is not None and current_mtime == self._mtime_ns:
            return self._config
        runtime = load_config(self._path, overrides=self._overrides)
        self._config = runtime
        self._mtime_ns = current_mtime
        self._logger.info("alert_rules_config.loaded", rules=len(runtime.rules), version=runtime.version)
        return runtime


CONFIG_MANAGER = AlertConfigManager()


__all__ = [
    "AlertRule",
    "AlertRuleDefaults",
    "AlertRulesRuntime",
    "AlertConfigManager",
    "CONFIG_MANAGER",
    "RuleType",
    "load_config",
    "parse_rule_overrides",
]
