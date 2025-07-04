import os
import time
import socket
import requests
import pytest


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.mark.skipif(not _port_open("localhost", 8000), reason="api not running")
def test_api_live_health() -> None:
    url = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000") + "/health"
    for _ in range(10):
        try:
            r = requests.get(url, timeout=0.5)
            if r.status_code == 200 and r.json() == {"db": "ok"}:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise AssertionError("API did not respond with healthy status")
