"""Guard against reintroducing the removed legacy ETL modules."""

from __future__ import annotations

import importlib
import importlib.util
import sys

import pytest


def _evict_legacy_module() -> None:
    for module in ("legacy", "etl.legacy"):
        sys.modules.pop(module, None)


@pytest.mark.parametrize("module_name", ("legacy", "etl.legacy"))
def test_legacy_package_spec_is_absent(module_name: str) -> None:
    """`legacy` modules must not be importable anywhere in the tree."""

    _evict_legacy_module()
    assert importlib.util.find_spec(module_name) is None


@pytest.mark.parametrize("module_name", ("legacy", "etl.legacy"))
def test_importing_legacy_raises(module_name: str) -> None:
    """Ensure imports fail loudly if someone re-adds the package via sys.path tweaks."""

    _evict_legacy_module()
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module_name)
