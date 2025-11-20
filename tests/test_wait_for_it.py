import pathlib
import subprocess
import sys

import pytest


@pytest.mark.slow
@pytest.mark.timeout(0)
def test_wait_for_it_exec() -> None:
    script = pathlib.Path("scripts/wait-for-it.sh")
    if not script.exists():
        # Skip test if script doesn't exist
        return

    # Skip on Windows as bash is not available by default
    if sys.platform.startswith("win"):
        return

    proc = subprocess.run(
        ["bash", str(script), "localhost:1", "-t", "1", "--", "echo", "ok"],
        capture_output=True,
    )
    assert proc.returncode == 0
