from datetime import datetime

import pytest
from fastapi import HTTPException

from services.api.routes import sku as sku_module
from services.api.schemas import SkuApprovalResponse, SkuResponse
from tests.unit.conftest import _StubResult, _StubSession


@pytest.mark.asyncio
async def test_get_sku_200():
    card_result = _StubResult(mappings=[{"title": "Sample SKU", "roi_pct": 12.5, "fees": 3.25}])
    chart_result = _StubResult(
        mappings=[
            {"date": "2024-01-03T00:00:00Z", "price": 15.0},
            {"date": "2024-01-01T00:00:00Z", "price": 12.5},
        ]
    )
    session = _StubSession(card_result, chart_result)

    payload = await sku_module.get_sku("B000TEST", session=session)

    assert isinstance(payload, SkuResponse)
    assert payload.title == "Sample SKU"
    assert isinstance(payload.roi, float) and payload.roi == pytest.approx(12.5)
    assert isinstance(payload.fees, float) and payload.fees == pytest.approx(3.25)
    assert isinstance(payload.chartData, list)
    assert payload.chartData[0].date <= payload.chartData[-1].date
    assert all(point.price is not None for point in payload.chartData)


@pytest.mark.asyncio
async def test_get_sku_404():
    session = _StubSession(_StubResult(mappings=[]))
    with pytest.raises(HTTPException) as exc:
        await sku_module.get_sku("MISSING", session=session)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_approve_idempotent(monkeypatch):
    calls = iter([1, 0])

    async def _fake_bulk(session, asins):
        return next(calls)

    monkeypatch.setattr(sku_module.roi_repository, "bulk_approve", _fake_bulk)
    session = _StubSession()

    first = await sku_module.approve_sku("B000TEST", session=session)
    second = await sku_module.approve_sku("B000TEST", session=session)

    assert isinstance(first, SkuApprovalResponse)
    assert isinstance(second, SkuApprovalResponse)
    assert first.changed == 1 and first.approved is True
    assert second.changed == 0 and second.approved is True


@pytest.mark.asyncio
async def test_get_sku_chart_empty_returns_empty_list():
    card_result = _StubResult(mappings=[{"title": "Empty SKU", "roi_pct": 5.0, "fees": 1.0}])
    session = _StubSession(card_result, _StubResult(mappings=[]))

    payload = await sku_module.get_sku("B000EMPTY", session=session)

    assert isinstance(payload, SkuResponse)
    assert payload.chartData == []


@pytest.mark.asyncio
async def test_get_sku_chart_datetime_serialization():
    dt = datetime(2024, 1, 5, 12, 30, 0)
    card_result = _StubResult(mappings=[{"title": "Time SKU", "roi_pct": 8.0, "fees": 2.0}])
    chart_result = _StubResult(mappings=[{"date": dt, "price": "17.5"}])
    session = _StubSession(card_result, chart_result)

    payload = await sku_module.get_sku("B000TIME", session=session)

    assert [point.model_dump() for point in payload.chartData] == [{"date": dt.isoformat(), "price": 17.5}]


@pytest.mark.asyncio
async def test_get_sku_invalid_view_returns_400(monkeypatch):
    def _raise_invalid(_: str = ""):
        raise sku_module.InvalidROIViewError("bad view")

    monkeypatch.setattr(sku_module, "_sku_card_sql", _raise_invalid)
    session = _StubSession(_StubResult(mappings=[]))
    with pytest.raises(HTTPException) as excinfo:
        await sku_module.get_sku("ANY", session=session)
    assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test_get_sku_chart_handles_invalid_values():
    card_result = _StubResult(mappings=[{"title": "Odd SKU", "roi_pct": 4.0, "fees": 0.5}])
    chart_result = _StubResult(mappings=[{"date": None, "price": object()}])
    session = _StubSession(card_result, chart_result)

    payload = await sku_module.get_sku("B000ODD", session=session)

    assert [point.model_dump() for point in payload.chartData] == [{"date": "", "price": 0.0}]
