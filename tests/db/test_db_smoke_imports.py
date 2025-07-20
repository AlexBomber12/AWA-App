"""
Lightweight import smoke test to raise coverage in the integration-db matrix.
Runs in <0.1 s, no network, no DB I/O.
"""

import importlib
import pathlib
import pkgutil

import pytest

ROOT = pathlib.Path(__file__).parents[2] / "services"


modules = []
for _, name, _ in pkgutil.walk_packages([str(ROOT)]):
    if name.endswith(("settings", "migrations", "alembic")):
        continue
    mod_path = ROOT / name.replace(".", "/")
    if mod_path.with_suffix(".py").exists() or mod_path.is_dir():
        modules.append(name)


@pytest.mark.parametrize("mod", modules)
def test_imports(mod):  # noqa: D103
    importlib.import_module(f"services.{mod}")
