from __future__ import annotations

import pytest

from packages.awa_common.files import sanitize_upload_name


def test_sanitize_upload_name_rejects_traversal() -> None:
    with pytest.raises(ValueError):
        sanitize_upload_name("../../etc/passwd.csv")


def test_sanitize_upload_name_rejects_leading_dot() -> None:
    with pytest.raises(ValueError):
        sanitize_upload_name(".env")


def test_sanitize_upload_name_normalises_unicode() -> None:
    name = "Ｆｉｌｅ.csv"
    assert sanitize_upload_name(name) == "File.csv"


def test_sanitize_upload_name_rejects_extension() -> None:
    with pytest.raises(ValueError):
        sanitize_upload_name("report.exe")


def test_sanitize_upload_name_cleans_weird_chars() -> None:
    result = sanitize_upload_name("Str@nGe Name!!.csv")
    assert result == "Str_nGe_Name.csv"


def test_sanitize_upload_name_default_when_empty() -> None:
    result = sanitize_upload_name("???////temp.csv")
    assert result.startswith("upload") or result.startswith("temp")
