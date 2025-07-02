import shutil
import subprocess
import time
import requests
import pytest

if shutil.which("docker") is None:
    pytest.skip("Docker not available in this runtime", allow_module_level=True)


def test_compose_up() -> None:
    subprocess.check_call("docker compose up -d --wait --wait-timeout 480", shell=True)
    time.sleep(5)
    assert requests.get("http://localhost:3000/").status_code == 200
    subprocess.run(["docker", "compose", "down"], check=False)
