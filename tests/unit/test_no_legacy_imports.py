"""Guard against reintroducing the removed legacy package."""

import importlib
import importlib.util
import sys

import pytest


def _evict_legacy_module() -> None:
    sys.modules.pop("legacy", None)


def test_legacy_package_spec_is_absent() -> None:
    """`legacy` must not be importable anywhere in the tree."""

    _evict_legacy_module()
    assert importlib.util.find_spec("legacy") is None


def test_importing_legacy_raises() -> None:
    """Ensure imports fail loudly if someone re-adds the package via sys.path tweaks."""

    _evict_legacy_module()
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("legacy")
