import subprocess
import pathlib
import sys


def test_wait_for_it_exec() -> None:
    script = pathlib.Path("services/etl/wait-for-it.sh")
    proc = subprocess.run([
        "bash",
        str(script),
        "localhost:0",
        "-t",
        "1",
        "--",
        "echo",
        "ok",
    ], capture_output=True)
    assert proc.returncode == 0
