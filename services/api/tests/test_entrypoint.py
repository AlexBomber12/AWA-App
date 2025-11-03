import subprocess
import sys
from pathlib import Path


def test_entrypoint_executes_without_env() -> None:
    # Skip on Windows as bash is not available by default
    if sys.platform.startswith("win"):
        return

    script = Path(__file__).resolve().parents[1] / "docker-entrypoint.sh"
    if not script.exists():
        return

    result = subprocess.run(["bash", str(script), "true"], capture_output=True)
    assert result.returncode == 0


def test_entrypoint_passthrough_exec() -> None:
    # Skip on Windows as bash is not available by default
    if sys.platform.startswith("win"):
        return

    script = Path(__file__).resolve().parents[1] / "docker-entrypoint.sh"
    if not script.exists():
        return

    result = subprocess.run(["bash", str(script), "echo", "hello"], capture_output=True, text=True)
    assert result.stdout.strip() == "hello"
