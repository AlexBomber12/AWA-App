import os
import socket

import httpx
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

API_URL = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")


def _port_open(host: str, port: int) -> bool:
    """Return True if TCP port is open; False otherwise (≤ 0.5 s timeout)."""
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


async def test_health_ok() -> None:
    if not _port_open("localhost", 8000):
        pytest.skip("API container is not running on localhost:8000")
    async with httpx.AsyncClient(base_url=API_URL) as client:
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_health(api_client: TestClient) -> None:
    r = api_client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
