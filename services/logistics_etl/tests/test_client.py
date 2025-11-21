import pytest
from httpx import Response

respx = pytest.importorskip("respx")

from services.logistics_etl import client  # noqa: E402


@respx.mock
@pytest.mark.asyncio
async def test_fetch_rates():
    csv_data = "lane,mode,eur_per_kg\nCN->DE,sea,1.5\n"
    route = respx.get(client.URL).mock(return_value=Response(200, text=csv_data))
    rows = await client.fetch_rates()
    assert route.called
    assert rows == [{"lane": "CN->DE", "mode": "sea", "eur_per_kg": 1.5}]


@pytest.mark.asyncio
async def test_download_with_retries_http_branch(monkeypatch):
    called: dict[str, object] = {}

    async def fake_http(url, timeout_s=None, retries=None):
        called["url"] = url
        called["retries"] = retries
        return b"data", {}

    monkeypatch.setenv("ETL_RETRY_ATTEMPTS", "2")
    monkeypatch.setattr(client, "_download_http", fake_http, raising=False)
    body, meta = await client._download_with_retries("http://example.com/data.csv", timeout_s=1, retries=2)
    assert body == b"data"
    assert called["retries"] == 2
