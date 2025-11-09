from __future__ import annotations

from typing import Any

import pytest

from services.api.routes import stats
from services.api.schemas import ReturnsStatsResponse


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]], scalar_value: Any = None) -> None:
        self._rows = rows
        self._scalar_value = scalar_value

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def scalar(self):
        return self._scalar_value


class _FakeDB:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.last_query = ""
        self.last_params: dict[str, Any] | None = None

    async def execute(self, sql, params=None):
        self.last_query = str(sql)
        self.last_params = dict(params or {})
        if "information_schema" in self.last_query:
            return _FakeResult([], scalar_value=1)
        return _FakeResult(self._rows)


@pytest.fixture(autouse=True)
def _reset_vendor_cache():
    stats._RETURNS_VENDOR_COLUMN = None
    yield
    stats._RETURNS_VENDOR_COLUMN = None


@pytest.mark.asyncio
async def test_returns_filters_apply(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")

    async def _always_true(_session):
        return True

    monkeypatch.setattr(stats, "_returns_vendor_available", _always_true)
    fake_db = _FakeDB(
        [
            {"asin": "A1", "qty": 2, "refund_amount": 5.5},
        ]
    )

    result = await stats.returns_stats(
        date_from="2024-01-01",
        date_to="2024-01-31",
        asin="A1",
        vendor="V100",
        session=fake_db,
    )

    assert "return_date >= :date_from" in fake_db.last_query
    assert "return_date <= :date_to" in fake_db.last_query
    assert "asin = :asin" in fake_db.last_query
    assert "vendor = :vendor" in fake_db.last_query
    assert fake_db.last_params == {
        "date_from": "2024-01-01",
        "date_to": "2024-01-31",
        "asin": "A1",
        "vendor": "V100",
    }
    assert isinstance(result, ReturnsStatsResponse)
    assert result.total_returns == 1
    assert result.items[0].asin == "A1"
    assert result.items[0].qty == 2
    assert result.items[0].refund_amount == pytest.approx(5.5)
    monkeypatch.delenv("STATS_USE_SQL", raising=False)


@pytest.mark.asyncio
async def test_returns_no_filters_preserves_shape(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    fake_db = _FakeDB(
        [
            {"asin": "B2", "qty": 1, "refund_amount": 1.2},
        ]
    )

    result = await stats.returns_stats(session=fake_db)
    assert "WHERE" not in fake_db.last_query.upper()
    assert isinstance(result, ReturnsStatsResponse)
    assert result.total_returns == 1
    assert result.items[0].asin == "B2"
    assert result.items[0].qty == 1
    assert result.items[0].refund_amount == pytest.approx(1.2)
    monkeypatch.delenv("STATS_USE_SQL", raising=False)
