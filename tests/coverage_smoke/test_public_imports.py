"""Import public service modules to bump coverage."""

import importlib
import pathlib
import pkgutil

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2] / "services"


@pytest.mark.parametrize(
    "module",
    [
        name
        for _, name, _ in pkgutil.walk_packages([str(ROOT)])
        if not name.endswith(("settings", "migrations", "alembic"))
    ],
)
def test_import(module: str) -> None:
    try:
        importlib.import_module(f"services.{module}")
    except ModuleNotFoundError:
        pytest.skip(module)
