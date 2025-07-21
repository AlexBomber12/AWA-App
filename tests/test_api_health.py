import shutil
import subprocess
import time

import pytest
import requests


from collections.abc import Generator


@pytest.fixture(scope="session", autouse=True)
def _api_container() -> Generator[None, None, None]:
    if not shutil.which("docker"):
        pytest.skip("docker not available")
    proc = subprocess.Popen(["docker", "compose", "up", "-d", "--wait", "api"])
    proc.wait()
    yield
    subprocess.run(["docker", "compose", "down", "-v"], check=False)


def test_health() -> None:  # noqa: D103
    url = "http://localhost:8000/health"
    for _ in range(15):
        try:
            assert requests.get(url, timeout=1).status_code == 200
            return
        except Exception:
            time.sleep(1)
    pytest.fail(f"{url} not reachable within 15 s")
