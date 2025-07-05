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
