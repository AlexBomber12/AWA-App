import datetime
from dataclasses import dataclass

import pytest

from services.api.routes import stats as stats_module
from services.api.schemas import (
    ReturnsStatsResponse,
    RoiByVendorResponse,
    RoiTrendResponse,
    StatsKPIResponse,
)


class DummyMappings:
    def __init__(self, rows):
        self.rows = rows

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return self.rows


class DummyDB:
    def __init__(self, results):
        self.results = results
        self.calls = []

    async def execute(self, stmt):
        key = str(stmt)
        self.calls.append(key)
        return DummyResult(self.results.get(key, []))


class DummyResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return DummyMappings(self._rows)


@pytest.mark.asyncio
async def test_kpi_sql_branch(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module, "current_roi_view", lambda: "v_roi_full")
    rows = [{"roi_avg": 1.5, "products": 2, "vendors": 1}]
    db = DummyDB({"SELECT AVG": rows})

    async def fake_execute(stmt):
        return DummyResult(rows)

    db.execute = fake_execute
    result = await stats_module.kpi(session=db)
    assert isinstance(result, StatsKPIResponse)
    assert result.kpi.roi_avg == 1.5


@pytest.mark.asyncio
async def test_roi_by_vendor_returns_items(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module, "current_roi_view", lambda: "v_roi_full")
    rows = [
        {"vendor": "A", "roi_avg": 2.5, "items": 3},
        {"vendor": "B", "roi_avg": None, "items": None},
    ]

    class DummyDB2:
        async def execute(self, stmt):
            return DummyResult(rows)

    resp = await stats_module.roi_by_vendor(session=DummyDB2())
    assert isinstance(resp, RoiByVendorResponse)
    assert resp.total_vendors == 2
    assert resp.items[0].vendor == "A"


@pytest.mark.asyncio
async def test_roi_trend_handles_multiple_columns(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module, "current_roi_view", lambda: "v_roi_full")
    calls = {"dt": RuntimeError("no column"), "date": RuntimeError("nope")}

    class DummyDB3:
        async def execute(self, stmt):
            text = str(stmt)
            if "snapshot_date" in text:
                rows = [{"month": datetime.date(2024, 1, 1), "roi_avg": 1.2, "items": 5}]
                return DummyResult(rows)
            for key, exc in calls.items():
                if key in text:
                    raise exc
            return DummyResult([])

    resp = await stats_module.roi_trend(session=DummyDB3())
    assert isinstance(resp, RoiTrendResponse)
    assert resp.points[0].month == "2024-01-01"


@dataclass
class _ScalarResult:
    value: int

    def scalar(self) -> int:
        return self.value


class _ReturnMappings:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _ReturnResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return _ReturnMappings(self._rows)


class _ReturnsDB:
    def __init__(self, *, vendor_available: bool, rows: list[dict[str, object]]):
        self.vendor_available = vendor_available
        self.rows = rows
        self.queries: list[tuple[str, dict[str, object]]] = []
        self.schema_checks = 0

    async def execute(self, stmt, params=None):
        sql = str(stmt)
        if "information_schema.columns" in sql:
            self.schema_checks += 1
            return _ScalarResult(1 if self.vendor_available else 0)
        self.queries.append((sql, dict(params or {})))
        return _ReturnResult(self.rows)


@pytest.mark.asyncio
async def test_returns_stats_includes_vendor_when_available(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module, "_RETURNS_VENDOR_COLUMN", None)
    rows = [{"asin": "A1", "qty": 3, "refund_amount": 12.5}]
    db = _ReturnsDB(vendor_available=True, rows=rows)

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
    sql, params = db.queries[0]
    assert "vendor = :vendor" in sql
    assert params["vendor"] == "Acme"
    # global cache avoids re-checking schema
    await stats_module.returns_stats(vendor="Acme", session=db)
    assert db.schema_checks == 1


@pytest.mark.asyncio
async def test_returns_stats_ignores_vendor_when_column_missing(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module, "_RETURNS_VENDOR_COLUMN", None)
    rows = [{"asin": "B2", "qty": None, "refund_amount": None}]
    db = _ReturnsDB(vendor_available=False, rows=rows)

    resp = await stats_module.returns_stats(vendor="Acme", session=db)
    assert isinstance(resp, ReturnsStatsResponse)
    assert resp.total_returns == 1
    sql, params = db.queries[0]
    assert "vendor" not in params
    assert "vendor = :vendor" not in sql
