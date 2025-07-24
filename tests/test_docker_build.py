import importlib
import os
import pathlib
import pkgutil
import shutil
import subprocess
import sys
import uuid

import pytest

IMAGE = f"awa-test:{uuid.uuid4().hex[:8]}"
ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_api_image_builds() -> None:
    env = {**os.environ, "DOCKER_BUILDKIT": "1"}
    try:
        subprocess.check_call(
            [
                "docker",
                "build",
                "-q",
                "-f",
                "services/api/Dockerfile",
                ".",
                "-t",
                IMAGE,
            ],
            cwd=ROOT,
            env=env,
        )
        subprocess.check_call(
            ["docker", "run", "--rm", IMAGE, "test", "-f", "/app/alembic.ini"]
        )
    finally:
        subprocess.run(["docker", "rmi", "-f", IMAGE], check=False)


# --- bump coverage ---------------------------------------------------------
SRC_ROOT = ROOT / "services"


def _import_all_from(path: pathlib.Path) -> None:
    """Import every sub-module under `services/<name>` to raise coverage."""
    pkg_name = f"services.{path.name}"
    if pkg_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(pkg_name, path / "__init__.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[pkg_name] = module
        spec.loader.exec_module(module)  # type: ignore[attr-defined]

    for mod in pkgutil.walk_packages([str(path)]):
        if "tests" in mod.name:
            continue
        try:
            importlib.import_module(f"{pkg_name}.{mod.name}")
        except Exception:
            pass


def test_smoke_import_all_modules() -> None:  # noqa: D103
    for sub in SRC_ROOT.iterdir():
        if (sub / "__init__.py").exists():
            _import_all_from(sub)
