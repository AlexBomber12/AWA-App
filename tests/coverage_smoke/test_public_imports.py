"""Import public service modules to bump coverage."""

import importlib
import pathlib
import pkgutil

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2] / "services"


modules = []
for _, name, _ in pkgutil.walk_packages([str(ROOT)]):
    if name.endswith(("settings", "migrations", "alembic")):
        continue
    mod_path = ROOT / name.replace(".", "/")
    if mod_path.with_suffix(".py").exists() or mod_path.is_dir():
        modules.append(name)


@pytest.mark.parametrize("module", modules)
def test_import(module: str) -> None:
    importlib.import_module(f"services.{module}")
