from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from services.alert_bot import worker as alerts_worker
from services.alert_bot.rules_store import FileRulesStore

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_yaml_thresholds_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rules_file = tmp_path / "alert_rules.yaml"
    rules_file.write_text(
        textwrap.dedent(
            """
            rules:
              - key: roi
                enabled: true
                thresholds:
                  min_roi: 9
              - key: buybox_drop_pct
                enabled: true
                thresholds:
                  drop_pct: 25
                  extra: 1
            """
        )
    )

    store = FileRulesStore(rules_file, enable_reload=False)
    monkeypatch.setattr(alerts_worker, "RULES_STORE", store)
    monkeypatch.setattr(alerts_worker, "TELEGRAM_ENABLED", True)

    seen_thresholds: dict[str, dict[str, int]] = {}

    async def roi_runner(thresholds):
        seen_thresholds["roi"] = thresholds
        return alerts_worker.RuleEvaluation(events=1, messages=["roi message"])

    async def buybox_runner(thresholds):
        seen_thresholds["buybox_drop_pct"] = thresholds
        return alerts_worker.RuleEvaluation(events=0, messages=[])

    monkeypatch.setitem(alerts_worker._RULE_HANDLERS, "roi", alerts_worker.RuleHandler("roi", roi_runner))
    monkeypatch.setitem(
        alerts_worker._RULE_HANDLERS,
        "buybox_drop_pct",
        alerts_worker.RuleHandler("buybox_drop_pct", buybox_runner),
    )

    sent_messages: list[str] = []

    async def fake_send(text: str, **kwargs):
        sent_messages.append(text)
        return True

    monkeypatch.setattr(alerts_worker, "send_message", fake_send)

    result = await alerts_worker.evaluate_alert_rules()
    assert result["notifications_sent"] == 1
    assert sent_messages == ["roi message"]
    assert seen_thresholds["roi"]["min_roi"] == 9
    assert seen_thresholds["buybox_drop_pct"]["drop_pct"] == 25
