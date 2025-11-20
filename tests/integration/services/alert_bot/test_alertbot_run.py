from __future__ import annotations

import asyncio
import textwrap
from pathlib import Path

import httpx
import pytest

from awa_common import http_client as http_client_module
from services.alert_bot import config as alert_config, worker
from services.alert_bot.config import AlertRule
from services.alert_bot.rules import AlertEvent
from services.worker import tasks


def _write_config(path: Path) -> Path:
    path.write_text(
        textwrap.dedent(
            """
            version: 1
            defaults:
              chat_id: "@ops"
            rules:
              - id: roi_drop
                type: roi_drop
                template: "Ping"
            """
        ),
        encoding="utf-8",
    )
    return path


@pytest.mark.integration
def test_alertbot_run_with_mocked_telegram(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = _write_config(tmp_path / "config.yaml")
    manager = alert_config.AlertConfigManager(path=config_path, watch=False)
    monkeypatch.setattr(alert_config, "CONFIG_MANAGER", manager)
    monkeypatch.setattr(worker.config_module, "CONFIG_MANAGER", manager)

    async def fake_rule(rule: AlertRule):
        return [AlertEvent(rule_id=rule.id, chat_ids=rule.chat_ids, text="hello", dedupe_key=f"{rule.id}:1")]

    monkeypatch.setattr(worker, "evaluate_rule", fake_rule)

    responses: list[str] = []

    def _mock_transport(request: httpx.Request) -> httpx.Response:
        responses.append(request.url.path)
        if request.url.path.endswith("getMe"):
            return httpx.Response(200, json={"ok": True, "result": {"username": "alertbot"}})
        if request.url.path.endswith("getChat"):
            return httpx.Response(200, json={"ok": True, "result": {"id": 1}})
        if request.url.path.endswith("sendMessage"):
            return httpx.Response(200, json={"ok": True})
        raise AssertionError(f"unexpected path {request.url.path}")

    transport = httpx.MockTransport(_mock_transport)
    clients: list[httpx.AsyncClient] = []

    def _async_client_factory(*args, **kwargs):
        client = httpx.AsyncClient(transport=transport, timeout=kwargs.get("timeout"))
        clients.append(client)
        return client

    monkeypatch.setattr(http_client_module.httpx, "AsyncClient", _async_client_factory, raising=False)

    monkeypatch.setattr(worker.settings, "TELEGRAM_TOKEN", "12345:ABCDE")
    monkeypatch.setattr(worker.settings, "TELEGRAM_DEFAULT_CHAT_ID", 999)
    monkeypatch.setattr(worker.settings, "ALERT_RULES_PATH", str(config_path))
    monkeypatch.setattr(worker.settings, "ALERT_RULES_SOURCE", "yaml")
    monkeypatch.setattr(worker.settings, "ALERT_RULES_FILE", str(config_path))
    monkeypatch.setattr(worker.settings, "ALERTS_ENABLED", True)
    monkeypatch.setattr(worker.settings, "ALERT_SEND_CONCURRENCY", 1)
    monkeypatch.setattr(worker.settings, "ALERT_EVAL_CONCURRENCY", 1)
    monkeypatch.setattr(worker.settings, "TELEGRAM_API_BASE", "http://127.0.0.1:0")

    runner = worker.AlertBotRunner()
    monkeypatch.setattr(worker, "RUNNER", runner)

    summary = tasks.alertbot_run()
    assert summary["notifications_sent"] == 1
    assert any(path.endswith("sendMessage") for path in responses)

    asyncio.run(asyncio.gather(*(client.aclose() for client in clients)))
