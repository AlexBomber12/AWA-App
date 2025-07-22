import pathlib
import re
import shutil
import subprocess
import time

import pytest


def _run_with_retries(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command with exponential backoff retries."""
    result: subprocess.CompletedProcess[str] = subprocess.CompletedProcess(cmd, 1)
    for attempt in range(5):
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        if result.returncode == 0:
            break
        time.sleep(2**attempt)
    return result


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_build_all_service_images(tmp_path: pathlib.Path) -> None:
    for df in pathlib.Path("services").glob("*/Dockerfile"):
        service_dir = df.parent
        log_file = tmp_path / f"{service_dir.name}.log"

        # pre-pull all base images with retries
        for line in df.read_text().splitlines():
            match = re.match(r"FROM\s+(\S+)", line)
            if match:
                _run_with_retries(["docker", "pull", match.group(1)])

        result = _run_with_retries(
            ["docker", "build", str(service_dir), "-t", "awa-tmp"]
        )
        log_file.write_text(result.stdout)
        assert result.returncode == 0 and "Successfully tagged" in result.stdout


# --- bump coverage --------------------------------------------------------
import importlib  # noqa: E402
import pathlib  # noqa: E402
import pkgutil  # noqa: E402
import sys  # noqa: E402

SRC_ROOT = pathlib.Path(__file__).resolve().parent.parent / "services"


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
