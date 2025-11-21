from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from services.alert_bot.config import AlertRule
from services.alert_bot.rules import AlertEvent


@dataclass(slots=True)
class RuleDecision:
    rule: AlertRule
    events: list[AlertEvent]


@dataclass(slots=True)
class NotificationIntent:
    rule_id: str
    severity: str
    message: str
    chat_ids: tuple[str, ...]
    parse_mode: str | None
    dedupe_key: str
    disable_web_page_preview: bool
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class AlertRequest:
    rule_id: str
    severity: str
    chat_id: str
    message: str
    parse_mode: str | None
    dedupe_key: str
    disable_web_page_preview: bool
    labels: dict[str, str] = field(default_factory=dict)


def dedupe_events(events: Iterable[AlertEvent]) -> list[AlertEvent]:
    seen: OrderedDict[str, AlertEvent] = OrderedDict()
    for event in events:
        if event.dedupe_key in seen:
            continue
        seen[event.dedupe_key] = event
    return list(seen.values())


def build_notification_intents(decisions: Sequence[RuleDecision]) -> list[NotificationIntent]:
    """Convert raw alert events into deterministic notification intents."""

    enriched: list[tuple[AlertEvent, AlertRule]] = []
    for decision in decisions:
        if not decision.events:
            continue
        for event in decision.events:
            enriched.append((event, decision.rule))
    if not enriched:
        return []
    deduped = dedupe_events(event for event, _ in enriched)
    intents: list[NotificationIntent] = []
    rule_lookup = {rule.id: rule for _, rule in enriched}
    for event in deduped:
        rule = rule_lookup.get(event.rule_id)
        severity = _resolve_severity(rule)
        labels = _intent_labels(rule)
        parse_mode = event.parse_mode or (rule.parse_mode if rule else None)
        intents.append(
            NotificationIntent(
                rule_id=event.rule_id,
                severity=severity,
                message=event.text,
                chat_ids=tuple(event.chat_ids),
                parse_mode=parse_mode,
                dedupe_key=event.dedupe_key,
                disable_web_page_preview=event.disable_web_page_preview,
                labels=labels,
            )
        )
    return intents


def build_alert_requests(decisions: Sequence[RuleDecision]) -> list[AlertRequest]:
    """Flatten notification intents into per-recipient alert requests."""

    intents = build_notification_intents(decisions)
    if not intents:
        return []
    requests: list[AlertRequest] = []
    for intent in intents:
        unique_chats = []
        for chat in intent.chat_ids:
            chat_id = str(chat).strip()
            if not chat_id or chat_id in unique_chats:
                continue
            unique_chats.append(chat_id)
        for chat_id in unique_chats:
            requests.append(
                AlertRequest(
                    rule_id=intent.rule_id,
                    severity=intent.severity,
                    chat_id=chat_id,
                    message=intent.message,
                    parse_mode=intent.parse_mode,
                    dedupe_key=intent.dedupe_key,
                    disable_web_page_preview=intent.disable_web_page_preview,
                    labels=dict(intent.labels),
                )
            )
    return requests


def _resolve_severity(rule: AlertRule | None) -> str:
    if rule is None:
        return "info"
    raw = str(rule.params.get("severity", "info")) if isinstance(rule.params, dict) else "info"
    normalized = raw.strip().lower()
    return normalized or "info"


def _intent_labels(rule: AlertRule | None) -> dict[str, str]:
    if rule is None:
        return {}
    labels: dict[str, str] = {}
    for key, value in (rule.params or {}).items():
        if key.startswith("label_"):
            labels[key.removeprefix("label_")] = str(value)
    return labels


__all__ = [
    "AlertRequest",
    "NotificationIntent",
    "RuleDecision",
    "build_alert_requests",
    "build_notification_intents",
    "dedupe_events",
]
