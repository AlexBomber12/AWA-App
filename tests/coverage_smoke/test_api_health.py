import os
import socket

import pytest
import requests


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.mark.skipif(not _port_open("localhost", 8000), reason="api not running")
def test_health_route() -> None:  # noqa: D103
    host = os.getenv("API_HOST", "http://localhost:8000")
    resp = requests.get(f"{host}/health", timeout=2)
    assert resp.status_code == 200
