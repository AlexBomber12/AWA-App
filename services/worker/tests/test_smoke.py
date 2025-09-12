import importlib
import pathlib  # noqa: F401
import sys  # noqa: F401

import pkg_resources  # noqa: F401
import pytest  # noqa: F401


def test_smoke():
    importlib.import_module("src")
