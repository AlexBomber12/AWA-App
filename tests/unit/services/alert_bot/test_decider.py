from dataclasses import replace

from services.alert_bot.config import AlertRule
from services.alert_bot.decider import (
    AlertRequest,
    NotificationIntent,
    RuleDecision,
    build_alert_requests,
    build_notification_intents,
)
from services.alert_bot.rules import AlertEvent


def _rule(**overrides: object) -> AlertRule:
    base = AlertRule(
        id="roi",
        type="roi_drop",
        enabled=True,
        schedule=None,
        chat_ids=["@ops"],
        parse_mode="HTML",
        params={"severity": "critical", "label_team": "ops"},
        template=None,
    )
    return replace(base, **overrides)


def test_build_notification_intents_dedupes_events() -> None:
    rule = _rule()
    events = [
        AlertEvent(rule_id="roi", chat_ids=["@ops"], text="alert", dedupe_key="roi:1"),
        AlertEvent(rule_id="roi", chat_ids=["@ops"], text="alert", dedupe_key="roi:1"),
    ]
    decisions = [RuleDecision(rule=rule, events=events)]
    intents = build_notification_intents(decisions)
    assert len(intents) == 1
    assert intents[0].severity == "critical"
    assert intents[0].labels.get("team") == "ops"


def test_build_notification_intents_handles_missing_rule() -> None:
    events = [AlertEvent(rule_id="missing", chat_ids=["@ops"], text="ping", dedupe_key="ping")]  # type: ignore[arg-type]
    decisions = [RuleDecision(rule=_rule(id="other"), events=[]), RuleDecision(rule=_rule(), events=events)]
    intents = build_notification_intents(decisions)
    assert intents
    assert intents[0].severity == "info"
    assert isinstance(intents[0], NotificationIntent)


def test_build_alert_requests_flattens_chats() -> None:
    rule = _rule(chat_ids=["chat1", "chat1", "chat2"])
    events = [AlertEvent(rule_id="roi", chat_ids=rule.chat_ids, text="alert", dedupe_key="roi:1")]
    decisions = [RuleDecision(rule=rule, events=events)]
    requests = build_alert_requests(decisions)
    assert isinstance(requests[0], AlertRequest)
    assert {req.chat_id for req in requests} == {"chat1", "chat2"}
    assert all(req.dedupe_key == "roi:1" for req in requests)


def test_build_alert_requests_empty_decisions() -> None:
    assert build_alert_requests([]) == []
