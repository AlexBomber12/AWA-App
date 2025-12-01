import importlib
import pathlib  # noqa: F401
import sys  # noqa: F401
from importlib.metadata import PackageNotFoundError, version

import pytest


def _ensure_metadata(dist: str = "pytest") -> None:
    try:
        version(dist)
    except PackageNotFoundError:
        pytest.skip(f"{dist} distribution metadata not available")


def test_smoke():
    _ensure_metadata()
    importlib.import_module("services.emailer")
