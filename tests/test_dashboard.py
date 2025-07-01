import shutil
import subprocess
import pytest

if shutil.which("docker") is None:
    pytest.skip("Docker not available", allow_module_level=True)


def test_compose_up() -> None:
    subprocess.check_call("docker compose up -d --wait --wait-timeout 180", shell=True)
    subprocess.run(["docker", "compose", "down"], check=False)
