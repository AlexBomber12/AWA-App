import importlib
import pathlib
import pkgutil

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREFIX = f"services.{ROOT.name}"


@pytest.mark.parametrize(
    "mod",
    [
        name
        for _, name, _ in pkgutil.walk_packages([str(ROOT)])
        if not name.endswith(("settings", "migrations", "alembic"))
        and ((ROOT / name.replace(".", "/")).with_suffix(".py").exists() or (ROOT / name.replace(".", "/")).is_dir())
    ],
)
def test_imports(mod):  # noqa: D103
    importlib.import_module(f"{PREFIX}.{mod}")
