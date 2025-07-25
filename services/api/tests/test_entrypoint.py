import subprocess
from pathlib import Path


def test_entrypoint_executes_without_env() -> None:
    script = Path(__file__).resolve().parents[1] / "entrypoint.sh"
    result = subprocess.run(["bash", str(script), "true"], capture_output=True)
    assert result.returncode == 0
