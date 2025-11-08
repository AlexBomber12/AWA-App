"""Import all service modules to surface lazy ImportErrors early."""

import importlib
import pathlib
import pkgutil

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3] / "services"


@pytest.mark.unit
@pytest.mark.parametrize(
    "mod",
    [
        name
        for _, name, _ in pkgutil.walk_packages([str(ROOT)])
        if not name.endswith(("settings", "migrations", "alembic"))
        and ((ROOT / name.replace(".", "/")).with_suffix(".py").exists() or (ROOT / name.replace(".", "/")).is_dir())
    ],
)
def test_imports_stay_healthy(mod: str) -> None:
    importlib.import_module(f"services.{mod}")
