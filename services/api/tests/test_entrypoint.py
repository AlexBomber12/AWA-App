import subprocess
from pathlib import Path


def test_entrypoint_executes_without_env() -> None:
    script = Path(__file__).resolve().parents[1] / "entrypoint.sh"
    result = subprocess.run(["bash", str(script), "true"], capture_output=True)
    assert result.returncode == 0


def test_entrypoint_passthrough_exec() -> None:
    script = Path(__file__).resolve().parents[1] / "entrypoint.sh"
    result = subprocess.run(
        ["bash", str(script), "echo", "hello"], capture_output=True, text=True
    )
    assert result.stdout.strip() == "hello"
