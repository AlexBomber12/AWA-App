from __future__ import annotations

import logging

import pytest

from packages.awa_common.settings import Settings


def _build_settings(regex: str) -> Settings:
    settings = Settings()
    settings.AUTH_REQUIRED_ROUTES_REGEX = regex
    return settings


def test_blank_regex_disables_protection() -> None:
    settings = _build_settings("")
    assert settings.should_protect_path("/any") is False


def test_valid_regex_matches_expected_routes() -> None:
    settings = _build_settings(r"^/api/(admin|ops)")
    assert settings.should_protect_path("/api/admin") is True
    assert settings.should_protect_path("/api/ops") is True
    assert settings.should_protect_path("/public") is False


def test_invalid_regex_fails_closed(caplog: pytest.LogCaptureFixture) -> None:
    settings = _build_settings("(*")
    with caplog.at_level(logging.WARNING):
        assert settings.should_protect_path("/any") is True
    assert any(
        "Invalid AUTH_REQUIRED_ROUTES_REGEX" in record.getMessage() for record in caplog.records
    )
    previous_log_count = len(caplog.records)
    assert settings.should_protect_path("/other") is True
    assert len(caplog.records) == previous_log_count
