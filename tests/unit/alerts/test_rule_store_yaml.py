from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from services.alert_bot.rules_store import FileRulesStore


def test_file_rules_store_parses_rules(tmp_path: Path) -> None:
    config_path = tmp_path / "rules.yaml"
    config_path.write_text(
        textwrap.dedent(
            """
            rules:
              - key: roi
                enabled: true
                schedule_cron: "*/10 * * * *"
                thresholds:
                  min_roi: 3
                channels:
                  telegram: true
              - key: returns_rate_pct
                enabled: false
                thresholds:
                  returns_pct: 7
            """
        )
    )
    store = FileRulesStore(config_path, enable_reload=False)
    rules = store.list_rules()
    assert len(rules) == 2
    assert rules[0].key == "roi"
    assert rules[0].thresholds["min_roi"] == 3
    assert rules[0].schedule_cron == "*/10 * * * *"
    assert rules[0].channel_enabled("telegram") is True
    assert rules[1].key == "returns_rate_pct"
    assert rules[1].enabled is False
    assert rules[1].schedule_cron is None


def test_file_rules_store_validates_entries(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        textwrap.dedent(
            """
            rules:
              - enabled: true
            """
        )
    )
    store = FileRulesStore(config_path, enable_reload=False)
    with pytest.raises(ValueError):
        store.list_rules()


def test_file_rules_store_missing_file(tmp_path: Path) -> None:
    config_path = tmp_path / "missing.yaml"
    store = FileRulesStore(config_path, enable_reload=False)
    with pytest.raises(FileNotFoundError):
        store.list_rules()


def test_file_rules_store_validates_channels_map(tmp_path: Path) -> None:
    config_path = tmp_path / "bad_channels.yaml"
    config_path.write_text(
        textwrap.dedent(
            """
            rules:
              - key: roi
                channels: 123
            """
        )
    )
    store = FileRulesStore(config_path, enable_reload=False)
    with pytest.raises(ValueError):
        store.list_rules()


def test_file_rules_store_reload(tmp_path: Path) -> None:
    config_path = tmp_path / "rules.yaml"
    config_path.write_text(
        textwrap.dedent(
            """
            rules:
              - key: roi
                enabled: true
            """
        )
    )
    store = FileRulesStore(config_path, enable_reload=True)
    assert store.list_rules()[0].key == "roi"
    config_path.write_text(
        textwrap.dedent(
            """
            rules:
              - key: returns_rate_pct
                enabled: true
            """
        )
    )
    # force reload by bumping mtime
    current = config_path.stat().st_mtime + 1
    os.utime(config_path, (current, current))
    assert store.list_rules()[0].key == "returns_rate_pct"
