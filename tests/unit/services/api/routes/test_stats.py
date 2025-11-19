import datetime
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import SQLAlchemyError

from services.api.routes import stats as stats_module
from services.api.schemas import (
    ReturnsStatsResponse,
    RoiByVendorResponse,
    RoiTrendResponse,
    StatsKPIResponse,
)
from tests.fakes import FakeRedis


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


def _fake_request(cache_client=None, namespace="stats:"):
    state = SimpleNamespace(stats_cache=cache_client, stats_cache_namespace=namespace)
    app = SimpleNamespace(state=state)
    return SimpleNamespace(app=app)


@pytest.mark.asyncio
async def test_kpi_handles_redis_errors(monkeypatch):
    class BrokenRedis:
        async def get(self, key):
            raise RuntimeError("boom")

    rows = [{"roi_avg": 1.0, "products": 1, "vendors": 1}]
    request = _fake_request(cache_client=BrokenRedis())
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
    rows = [{"asin": "A1", "qty": 3, "refund_amount": 12.5}]
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
    stmt, params = db.calls[0]
    compiled = str(stmt)
    assert "vendor" in compiled.lower()
    assert params["vendor"] == "Acme"
    await stats_module.returns_stats(vendor="Acme", session=db)
    assert vendor_calls == 2


@pytest.mark.asyncio
async def test_returns_stats_ignores_vendor_when_column_missing(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    rows = [{"asin": "B2", "qty": None, "refund_amount": None}]
    db = DummyDB(rows)

    async def _vendor_missing(session, table_name, schema):
        return False

    monkeypatch.setattr(stats_module, "returns_vendor_column_exists", _vendor_missing)

    resp = await stats_module.returns_stats(vendor="Acme", session=db)
    assert isinstance(resp, ReturnsStatsResponse)
    assert resp.total_returns == 1
    stmt, params = db.calls[0]
    if params is not None:
        assert "vendor" not in params
    assert "vendor" not in str(stmt)


def test_stats_namespace_defaults(monkeypatch):
    monkeypatch.setattr(stats_module.settings, "STATS_CACHE_NAMESPACE", "custom:", raising=False)
    assert stats_module._stats_cache_client(None) is None
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
    cache_client = FakeRedis()
    request = _fake_request(cache_client)
    rows = [{"asin": "C1", "qty": 5, "refund_amount": 7.5}]
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
    assert len(db.calls) == 1
    cache_keys = list(cache_client._kv.keys())
    assert any(key.startswith("stats:returns") for key in cache_keys)
    assert any(key.endswith(":meta") for key in cache_keys)
