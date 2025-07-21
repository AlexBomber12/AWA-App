import shutil
import subprocess
import time

import pytest
import requests


@pytest.fixture(scope="session", autouse=True)
def _api_container():
    if not shutil.which("docker"):
        pytest.skip("docker not available")
    proc = subprocess.Popen(["docker", "compose", "up", "-d", "--wait", "api"])
    proc.wait()
    yield
    subprocess.run(["docker", "compose", "down", "-v"], check=False)


def test_health() -> None:
    for _ in range(15):
        try:
            r = requests.get("http://localhost:8000/health", timeout=1)
            if r.status_code == 200:
                return
        except Exception:
            time.sleep(1)
    pytest.fail("health endpoint not ready in 15 s")
