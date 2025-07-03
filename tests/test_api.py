import httpx
import os
import pytest

API_URL = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")


@pytest.mark.asyncio
async def test_health_ok():
    async with httpx.AsyncClient(base_url=API_URL) as client:
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
