from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from services.alert_bot import config as alert_config


def _write_yaml(tmp_path: Path, contents: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(textwrap.dedent(contents), encoding="utf-8")
    return path


def test_load_config_merges_defaults(tmp_path: Path) -> None:
    path = _write_yaml(
        tmp_path,
        """
        version: 1
        defaults:
          enabled: true
          chat_id: "@ops"
          parse_mode: HTML
        rules:
          - id: roi_drop
            type: roi_drop
            schedule: "@every 5m"
            params:
              min_roi_pct: 4
        """,
    )
    runtime = alert_config.load_config(path)
    rules = runtime.enabled_rules()
    assert len(rules) == 1
    rule = rules[0]
    assert rule.chat_ids == ["@ops"]
    assert rule.params["min_roi_pct"] == 4
    assert rule.schedule == "@every 5m"


def test_load_config_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = _write_yaml(
        tmp_path,
        """
        version: 1
        defaults:
          chat_id: "@ops"
        rules:
          - id: roi_drop
            type: roi_drop
          - id: roi_drop
            type: roi_drop
        """,
    )
    with pytest.raises(ValueError, match="Duplicate rule id"):
        alert_config.load_config(path)


def test_load_config_requires_chat_ids(tmp_path: Path) -> None:
    path = _write_yaml(
        tmp_path,
        """
        version: 1
        rules:
          - id: roi_drop
            type: roi_drop
        """,
    )
    with pytest.raises(ValueError, match="does not define chat_id"):
        alert_config.load_config(path)


def test_parse_rule_overrides_applies(tmp_path: Path) -> None:
    overrides = alert_config.parse_rule_overrides("roi_drop:off,buybox_loss:on")
    path = _write_yaml(
        tmp_path,
        """
        version: 1
        defaults:
          chat_id: "@ops"
        rules:
          - id: roi_drop
            type: roi_drop
          - id: buybox_loss
            type: buybox_loss
        """,
    )
    runtime = alert_config.load_config(path, overrides=overrides)
    status = {rule.id: rule.enabled for rule in runtime.rules}
    assert status["roi_drop"] is False
    assert status["buybox_loss"] is True


def test_runtime_chat_ids(tmp_path: Path) -> None:
    path = _write_yaml(
        tmp_path,
        """
        version: 2
        defaults:
          chat_id: "@ops"
        rules:
          - id: roi_drop
            type: roi_drop
          - id: buybox_loss
            type: buybox_loss
            enabled: false
        """,
    )
    runtime = alert_config.load_config(path)
    assert runtime.chat_ids() == {"@ops"}


def test_config_manager_reload_detects_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(alert_config.signal, "signal", lambda *args, **kwargs: None)
    monkeypatch.setattr(alert_config.AlertConfigManager, "_signal_installed", False, raising=False)
    path = _write_yaml(
        tmp_path,
        """
        version: 1
        defaults:
          chat_id: "@ops"
        rules:
          - id: roi_drop
            type: roi_drop
        """,
    )
    manager = alert_config.AlertConfigManager(path=path, watch=True, watch_interval=0.0)
    first = manager.load(force=True)
    assert first is not None
    path.write_text(
        textwrap.dedent(
            """
            version: 2
            defaults:
              chat_id: "@ops"
            rules:
              - id: roi_drop
                type: roi_drop
                enabled: false
            """
        ),
        encoding="utf-8",
    )
    manager.request_reload()
    updated = manager.maybe_reload()
    assert updated is not None
    assert updated.version == "2"


def test_coerce_chat_list_and_normalize_id() -> None:
    assert alert_config._normalize_rule_id(" ROI ") == "roi"  # type: ignore[attr-defined]
    chats = alert_config._coerce_chat_list(["@ops", "  "])  # type: ignore[attr-defined]
    assert chats == ["@ops"]


def test_config_manager_no_watch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(alert_config.signal, "signal", lambda *args, **kwargs: None)
    monkeypatch.setattr(alert_config.AlertConfigManager, "_signal_installed", False, raising=False)
    path = _write_yaml(
        tmp_path,
        """
        version: 1
        defaults:
          chat_id: "@ops"
        rules:
          - id: roi_drop
            type: roi_drop
        """,
    )
    manager = alert_config.AlertConfigManager(path=path, watch=False)
    runtime = manager.load(force=True)
    assert runtime is not None
    assert manager.maybe_reload() is runtime
