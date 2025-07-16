import shutil
import subprocess
import time

import pytest
import requests  # type: ignore

if shutil.which("docker") is None or shutil.which("docker-compose") is None:
    pytest.skip("Docker is not installed on this runner", allow_module_level=True)


def test_compose_up() -> None:
    subprocess.check_call("docker compose up -d --wait --wait-timeout 480", shell=True)
    time.sleep(5)
    assert requests.get("http://localhost:3000/").status_code == 200
    subprocess.run(["docker", "compose", "down"], check=False)
