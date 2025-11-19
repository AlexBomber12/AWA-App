import datetime
from types import SimpleNamespace
from typing import Any

import pytest
from cashews.exceptions import CacheBackendInteractionError
from sqlalchemy.exc import SQLAlchemyError

from awa_common import cache as cache_module
from services.api.routes import stats as stats_module
from services.api.schemas import (
    ReturnsStatsResponse,
    RoiByVendorResponse,
    RoiTrendResponse,
    StatsKPIResponse,
)


@pytest.fixture(autouse=True)
def disable_stats_cache(monkeypatch):
    monkeypatch.setattr(stats_module.settings, "STATS_ENABLE_CACHE", False, raising=False)


class DummyMappings:
    def __init__(self, rows):
        self._rows = rows

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return list(self._rows)


class DummyResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return DummyMappings(self._rows)


class DummyDB:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []

    async def execute(self, stmt, params=None):
        self.calls.append((stmt, params))
        return DummyResult(self.rows)


def _fake_request(namespace="stats:"):
    state = SimpleNamespace(stats_cache=None, stats_cache_namespace=namespace)
    app = SimpleNamespace(state=state)
    return SimpleNamespace(app=app)


def _returns_row(
    asin: str,
    qty: int,
    refund: float,
    *,
    total: int | None = None,
    total_units: int | None = None,
    total_refund: float | None = None,
) -> dict[str, Any]:
    total_count = total if total is not None else 1
    units = total_units if total_units is not None else qty
    refund_total = total_refund if total_refund is not None else refund
    return {
        "asin": asin,
        "qty": qty,
        "refund_amount": refund,
        "total_count": total_count,
        "total_units": units,
        "total_refund": refund_total,
        "top_asin": asin,
        "top_refund": refund_total,
    }


@pytest.mark.asyncio
async def test_kpi_handles_redis_errors(monkeypatch):
    monkeypatch.setattr(stats_module.settings, "STATS_ENABLE_CACHE", True, raising=False)
    await cache_module.cache.clear()

    async def broken_get(*_args, **_kwargs):
        raise CacheBackendInteractionError()

    rows = [{"roi_avg": 1.0, "products": 1, "vendors": 1}]
    monkeypatch.setattr(cache_module.cache, "get", broken_get, raising=False)
    request = _fake_request()
    result = await stats_module.kpi(session=DummyDB(rows), request=request)
    assert isinstance(result, StatsKPIResponse)


@pytest.mark.asyncio
async def test_kpi_sql_branch(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module, "get_roi_view_name", lambda: "v_roi_full")
    rows = [{"roi_avg": 1.5, "products": 2, "vendors": 1}]
    db = DummyDB(rows)
    result = await stats_module.kpi(session=db)
    assert isinstance(result, StatsKPIResponse)
    assert result.kpi.roi_avg == 1.5


@pytest.mark.asyncio
async def test_roi_by_vendor_returns_items(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module, "get_roi_view_name", lambda: "v_roi_full")
    rows = [
        {"vendor": "A", "roi_avg": 2.5, "items": 3},
        {"vendor": "B", "roi_avg": None, "items": None},
    ]

    resp = await stats_module.roi_by_vendor(session=DummyDB(rows))
    assert isinstance(resp, RoiByVendorResponse)
    assert resp.total_vendors == 2
    assert resp.items[0].vendor == "A"


@pytest.mark.asyncio
async def test_roi_trend_handles_multiple_columns(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module, "get_roi_view_name", lambda: "v_roi_full")

    class TrendDB:
        def __init__(self):
            self.calls = 0

        async def execute(self, stmt, params=None):
            self.calls += 1
            if self.calls < 3:
                raise SQLAlchemyError("missing column")
            rows = [{"month": datetime.date(2024, 1, 1), "roi_avg": 1.2, "items": 5}]
            return DummyResult(rows)

    resp = await stats_module.roi_trend(session=TrendDB())
    assert isinstance(resp, RoiTrendResponse)
    assert resp.points[0].month == "2024-01-01"


@pytest.mark.asyncio
async def test_kpi_invalid_view_returns_400(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")

    def _raise_invalid():
        raise stats_module.InvalidROIViewError("bad view")

    monkeypatch.setattr(stats_module, "get_roi_view_name", _raise_invalid)
    with pytest.raises(stats_module.HTTPException) as excinfo:
        await stats_module.kpi(session=DummyDB({}))
    assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test_roi_by_vendor_invalid_view_returns_400(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(
        stats_module,
        "get_roi_view_name",
        lambda: (_ for _ in ()).throw(stats_module.InvalidROIViewError("nope")),
    )
    with pytest.raises(stats_module.HTTPException) as excinfo:
        await stats_module.roi_by_vendor(session=DummyDB({}))
    assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test_roi_trend_invalid_view_returns_400(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")

    def _raise_invalid():
        raise stats_module.InvalidROIViewError("bad view")

    monkeypatch.setattr(stats_module, "get_roi_view_name", _raise_invalid)
    with pytest.raises(stats_module.HTTPException) as excinfo:
        await stats_module.roi_trend(session=DummyDB({}))
    assert excinfo.value.status_code == 400


@pytest.mark.asyncio
async def test_kpi_returns_defaults_without_sql(monkeypatch):
    monkeypatch.delenv("STATS_USE_SQL", raising=False)
    result = await stats_module.kpi(session=DummyDB({}))
    assert result.kpi.products == 0


@pytest.mark.asyncio
async def test_roi_by_vendor_returns_empty_without_sql(monkeypatch):
    monkeypatch.delenv("STATS_USE_SQL", raising=False)
    resp = await stats_module.roi_by_vendor(session=DummyDB({}))
    assert resp.items == []


@pytest.mark.asyncio
async def test_roi_trend_returns_empty_without_sql(monkeypatch):
    monkeypatch.delenv("STATS_USE_SQL", raising=False)
    resp = await stats_module.roi_trend(session=DummyDB({}))
    assert resp.points == []


@pytest.mark.asyncio
async def test_returns_stats_includes_vendor_when_available(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    rows = [_returns_row("A1", 3, 12.5)]
    db = DummyDB(rows)
    vendor_calls = 0

    async def _vendor_exists(session, table_name, schema):
        nonlocal vendor_calls
        vendor_calls += 1
        return True

    monkeypatch.setattr(stats_module, "returns_vendor_column_exists", _vendor_exists)

    resp = await stats_module.returns_stats(
        date_from="2024-01-01",
        date_to="2024-02-01",
        asin="A1",
        vendor="Acme",
        session=db,
    )
    assert isinstance(resp, ReturnsStatsResponse)
    assert resp.total_returns == 1
    assert resp.items[0].qty == 3
    assert resp.pagination.total == 1
    assert resp.summary.total_units == 3
    stmt, params = db.calls[0]
    compiled = str(stmt)
    assert "vendor" in compiled.lower()
    assert params["vendor"] == "Acme"
    await stats_module.returns_stats(vendor="Acme", session=db)
    assert vendor_calls == 2


@pytest.mark.asyncio
async def test_returns_stats_ignores_vendor_when_column_missing(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    rows = [_returns_row("B2", 0, 0.0)]
    db = DummyDB(rows)

    async def _vendor_missing(session, table_name, schema):
        return False

    monkeypatch.setattr(stats_module, "returns_vendor_column_exists", _vendor_missing)

    resp = await stats_module.returns_stats(vendor="Acme", session=db)
    assert isinstance(resp, ReturnsStatsResponse)
    assert resp.total_returns == 1
    assert resp.pagination.total == 1
    stmt, params = db.calls[0]
    if params is not None:
        assert "vendor" not in params
    assert "vendor" not in str(stmt)


def test_stats_namespace_defaults(monkeypatch):
    monkeypatch.setattr(stats_module.settings, "STATS_CACHE_NAMESPACE", "custom:", raising=False)
    assert stats_module._stats_namespace(None) == "custom:"


@pytest.mark.asyncio
async def test_returns_stats_invalid_date(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    with pytest.raises(stats_module.HTTPException):
        await stats_module.returns_stats(date_from="invalid", session=DummyDB([]))


@pytest.mark.asyncio
async def test_returns_stats_uses_cache(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module.settings, "STATS_ENABLE_CACHE", True, raising=False)
    monkeypatch.setattr(stats_module.settings, "STATS_CACHE_TTL_S", 5, raising=False)
    await cache_module.cache.clear()
    request = _fake_request()
    rows = [_returns_row("C1", 5, 7.5)]
    db = DummyDB(rows)

    resp1 = await stats_module.returns_stats(
        date_from="2024-01-01",
        date_to="2024-01-02",
        session=db,
        request=request,
    )
    resp2 = await stats_module.returns_stats(
        date_from="2024-01-01",
        date_to="2024-01-02",
        session=db,
        request=request,
    )
    assert resp1.total_returns == 1
    assert resp2.total_returns == 1
    assert resp1.summary.total_refund_amount == pytest.approx(7.5)
    assert len(db.calls) == 1
    from_keys = [key async for key in cache_module.cache.scan("stats:returns*", batch_size=10)]
    assert any(key.startswith("stats:returns") for key in from_keys)
    meta_found = False
    async for key in cache_module.cache.scan("stats:returns*:meta", batch_size=10):
        if key.endswith(":meta"):
            meta_found = True
            break
    assert meta_found
