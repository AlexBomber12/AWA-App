from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Protocol

import yaml  # type: ignore[import-untyped]

SUPPORTED_RULE_KEYS = {
    "roi",
    "price_increase_pct",
    "buybox_drop_pct",
    "returns_rate_pct",
    "stale_price_days",
}


@dataclass(slots=True)
class RuleConfig:
    key: str
    enabled: bool = True
    schedule_cron: str | None = None
    thresholds: dict[str, Any] = field(default_factory=dict)
    channels: dict[str, bool] = field(default_factory=dict)
    description: str | None = None

    def channel_enabled(self, name: str) -> bool:
        if not self.channels:
            return True
        return bool(self.channels.get(name, False))


class RulesStore(Protocol):
    """Interface for alert rule storage backends."""

    def list_rules(self) -> list[RuleConfig]: ...

    def get_rule(self, key: str) -> RuleConfig | None: ...

    def upsert_rule(self, rule: RuleConfig) -> RuleConfig: ...


class FileRulesStore(RulesStore):
    """Rule store backed by a YAML file, with optional hot reload."""

    def __init__(self, path: str | Path, *, enable_reload: bool = True) -> None:
        self._path = Path(path)
        self._enable_reload = enable_reload
        self._lock = Lock()
        self._cached_rules: list[RuleConfig] = []
        self._mtime_ns: int | None = None

    def list_rules(self) -> list[RuleConfig]:
        self._ensure_loaded()
        return [self._copy_rule(rule) for rule in self._cached_rules]

    def get_rule(self, key: str) -> RuleConfig | None:
        self._ensure_loaded()
        key_normalized = key.strip().lower()
        for rule in self._cached_rules:
            if rule.key == key_normalized:
                return self._copy_rule(rule)
        return None

    def upsert_rule(self, _rule: RuleConfig) -> RuleConfig:
        raise NotImplementedError("FileRulesStore is read-only; update the YAML file directly.")

    def _ensure_loaded(self) -> None:
        with self._lock:
            try:
                current_mtime = self._path.stat().st_mtime_ns
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"Alert rules file not found: {self._path}") from exc
            if self._cached_rules and (not self._enable_reload or current_mtime == self._mtime_ns):
                return
            data = self._load_yaml()
            self._cached_rules = self._parse_rules(data)
            self._mtime_ns = current_mtime

    def _load_yaml(self) -> dict[str, Any]:
        text = self._path.read_text(encoding="utf-8")
        loaded = yaml.safe_load(text) or {}
        if not isinstance(loaded, dict):
            raise ValueError("Alert rules file must contain a mapping at the root.")
        return loaded

    def _parse_rules(self, data: dict[str, Any]) -> list[RuleConfig]:
        raw_rules = data.get("rules")
        if not isinstance(raw_rules, list):
            raise ValueError("Alert rules file must define a top-level 'rules' list.")
        parsed: list[RuleConfig] = []
        for entry in raw_rules:
            if not isinstance(entry, dict):
                raise ValueError("Each rule entry must be a mapping.")
            key = (entry.get("key") or "").strip().lower()
            if not key:
                raise ValueError("Rule entry missing 'key'.")
            if key not in SUPPORTED_RULE_KEYS:
                raise ValueError(f"Unsupported rule key: {key}")
            enabled = bool(entry.get("enabled", True))
            schedule = entry.get("schedule_cron")
            if schedule is not None and not isinstance(schedule, str):
                raise ValueError(f"schedule_cron for rule '{key}' must be a string when provided.")
            thresholds = entry.get("thresholds") or {}
            if not isinstance(thresholds, dict):
                raise ValueError(f"thresholds for rule '{key}' must be a mapping.")
            channels = entry.get("channels") or {}
            if channels and not isinstance(channels, dict):
                raise ValueError(f"channels for rule '{key}' must be a mapping.")
            normalized_channels = {str(name): bool(value) for name, value in channels.items()}
            description = entry.get("description")
            if description is not None and not isinstance(description, str):
                raise ValueError(f"description for rule '{key}' must be a string when provided.")
            parsed.append(
                RuleConfig(
                    key=key,
                    enabled=enabled,
                    schedule_cron=schedule,
                    thresholds=dict(thresholds),
                    channels=normalized_channels,
                    description=description,
                )
            )
        return parsed

    @staticmethod
    def _copy_rule(rule: RuleConfig) -> RuleConfig:
        return RuleConfig(
            key=rule.key,
            enabled=rule.enabled,
            schedule_cron=rule.schedule_cron,
            thresholds=dict(rule.thresholds),
            channels=dict(rule.channels),
            description=rule.description,
        )


class DbRulesStore(RulesStore):
    """Placeholder for future DB-backed rule storage."""

    def list_rules(self) -> list[RuleConfig]:
        raise NotImplementedError("DbRulesStore is not implemented yet.")

    def get_rule(self, key: str) -> RuleConfig | None:
        raise NotImplementedError("DbRulesStore is not implemented yet.")

    def upsert_rule(self, rule: RuleConfig) -> RuleConfig:
        raise NotImplementedError("DbRulesStore is not implemented yet.")


__all__ = ["RuleConfig", "RulesStore", "FileRulesStore", "DbRulesStore", "SUPPORTED_RULE_KEYS"]
