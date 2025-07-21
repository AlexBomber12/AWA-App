import socket
import time

import pytest
import requests

URL = "http://localhost:8000/health"


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.mark.skipif(not _port_open("localhost", 8000), reason="api not running")
def test_health():  # noqa: D103
    for _ in range(20):
        try:
            if requests.get(URL, timeout=1).status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    pytest.fail("/health not ready after 20 s")
