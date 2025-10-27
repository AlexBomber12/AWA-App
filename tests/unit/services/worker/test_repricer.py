from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from services.worker.repricer.app import logic, main, schemas


def test_compute_price_calculates_margin():
    price = logic.compute_price("ASIN123456", Decimal("10"), Decimal("2"))
    assert price == Decimal("14.12")


@pytest.mark.asyncio
async def test_price_endpoint_returns_response():
    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/price", json={"asin": "ASIN123456", "our_cost": "10", "fee_estimate": "2"}
        )
        body = resp.json()
        assert body["new_price"]
        assert body["asin"] == "ASIN123456"


@pytest.mark.asyncio
async def test_full_generates_responses():
    class DummyResult:
        def __init__(self, rows):
            self._rows = rows

        def fetchall(self):
            return self._rows

    class DummySession:
        async def execute(self, stmt):
            return DummyResult([("ASIN0000001", Decimal("10"), Decimal("1"))])

    responses = await main.full(DummySession())
    assert responses[0].asin == "ASIN0000001"


def test_price_request_validation():
    with pytest.raises(ValidationError):
        schemas.PriceRequest(asin="short", our_cost=1, fee_estimate=0)
