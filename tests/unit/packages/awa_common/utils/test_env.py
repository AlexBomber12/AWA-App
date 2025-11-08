from __future__ import annotations

import pytest

from awa_common.utils import env as env_utils


def test_env_int_reads_value(monkeypatch):
    monkeypatch.setenv("TMP_INT", "42")
    assert env_utils.env_int("TMP_INT") == 42


def test_env_int_uses_default_and_bounds(monkeypatch):
    monkeypatch.delenv("TMP_INT", raising=False)
    assert env_utils.env_int("TMP_INT", default=5, min=1, max=10) == 5


def test_env_int_raises_when_missing(monkeypatch):
    monkeypatch.delenv("TMP_INT", raising=False)
    with pytest.raises(ValueError):
        env_utils.env_int("TMP_INT")


def test_env_int_raises_on_bounds(monkeypatch):
    monkeypatch.setenv("TMP_INT", "1")
    with pytest.raises(ValueError):
        env_utils.env_int("TMP_INT", min=2)


def test_env_float_reads_value(monkeypatch):
    monkeypatch.setenv("TMP_FLOAT", "3.14")
    assert env_utils.env_float("TMP_FLOAT", min=0, max=10) == pytest.approx(3.14)


def test_env_float_uses_default(monkeypatch):
    monkeypatch.delenv("TMP_FLOAT", raising=False)
    assert env_utils.env_float("TMP_FLOAT", default=1.25) == pytest.approx(1.25)


def test_env_bool_reads_truthy(monkeypatch):
    monkeypatch.setenv("TMP_BOOL", "YES")
    assert env_utils.env_bool("TMP_BOOL") is True


def test_env_bool_reads_falsey(monkeypatch):
    monkeypatch.setenv("TMP_BOOL", "0")
    assert env_utils.env_bool("TMP_BOOL") is False


def test_env_bool_default(monkeypatch):
    monkeypatch.delenv("TMP_BOOL", raising=False)
    assert env_utils.env_bool("TMP_BOOL", default=True) is True


def test_env_bool_invalid(monkeypatch):
    monkeypatch.setenv("TMP_BOOL", "maybe")
    with pytest.raises(ValueError):
        env_utils.env_bool("TMP_BOOL")


def test_env_str(monkeypatch):
    monkeypatch.delenv("TMP_STR", raising=False)
    assert env_utils.env_str("TMP_STR") is None
    monkeypatch.setenv("TMP_STR", "  value  ")
    assert env_utils.env_str("TMP_STR") == "value"
    assert env_utils.env_str("TMP_STR", strip=False) == "  value  "
