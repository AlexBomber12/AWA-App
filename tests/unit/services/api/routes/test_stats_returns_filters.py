from __future__ import annotations

import datetime as dt
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
        self.last_statement = None
        self.last_query = ""
        self.last_params: dict[str, Any] | None = None

    async def execute(self, sql, params=None):
        self.last_statement = sql
        self.last_query = str(sql)
        self.last_params = dict(params or {})
        return _FakeResult(self._rows)


def _returns_row(
    asin: str,
    qty: int,
    refund: float,
    total: int = 1,
) -> dict[str, Any]:
    return {
        "asin": asin,
        "qty": qty,
        "refund_amount": refund,
        "total_count": total,
        "total_units": qty,
        "total_refund": refund,
        "top_asin": asin,
        "top_refund": refund,
    }


@pytest.mark.asyncio
async def test_returns_filters_apply(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")

    async def _always_true(_session, **_kwargs):
        return True

    monkeypatch.setattr(stats, "returns_vendor_column_exists", _always_true)
    fake_db = _FakeDB([_returns_row("A1", 2, 5.5)])

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
        "date_from": dt.date(2024, 1, 1),
        "date_to": dt.date(2024, 1, 31),
        "asin": "A1",
        "vendor": "V100",
    }
    assert isinstance(result, ReturnsStatsResponse)
    assert result.total_returns == 1
    assert result.items[0].asin == "A1"
    assert result.items[0].qty == 2
    assert result.items[0].refund_amount == pytest.approx(5.5)
    assert result.pagination.total == 1
    assert result.summary.total_refund_amount == pytest.approx(5.5)
    monkeypatch.delenv("STATS_USE_SQL", raising=False)


@pytest.mark.asyncio
async def test_returns_no_filters_preserves_shape(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    fake_db = _FakeDB([_returns_row("B2", 1, 1.2)])

    result = await stats.returns_stats(session=fake_db)
    assert "WHERE" not in fake_db.last_query.upper()
    assert isinstance(result, ReturnsStatsResponse)
    assert result.total_returns == 1
    assert result.items[0].asin == "B2"
    assert result.items[0].qty == 1
    assert result.items[0].refund_amount == pytest.approx(1.2)
    assert result.pagination.total == 1
    monkeypatch.delenv("STATS_USE_SQL", raising=False)


@pytest.mark.asyncio
async def test_stats_guardrails_clamp(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats.settings, "STATS_MAX_DAYS", 5, raising=False)
    monkeypatch.setattr(stats.settings, "REQUIRE_CLAMP", False, raising=False)
    fake_db = _FakeDB([_returns_row("C1", 10, 12.0)])

    result = await stats.returns_stats(
        date_from="2024-01-01",
        date_to="2024-02-01",
        session=fake_db,
    )

    assert fake_db.last_params is not None
    assert fake_db.last_params["date_from"] == dt.date(2024, 1, 28)
    assert fake_db.last_params["date_to"] == dt.date(2024, 2, 1)
    assert result.total_returns == 1
    assert result.pagination.page == 1
    monkeypatch.delenv("STATS_USE_SQL", raising=False)


@pytest.mark.asyncio
async def test_stats_guardrails_require_error(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats.settings, "STATS_MAX_DAYS", 3, raising=False)
    monkeypatch.setattr(stats.settings, "REQUIRE_CLAMP", True, raising=False)
    fake_db = _FakeDB([])

    with pytest.raises(stats.HTTPException):
        await stats.returns_stats(
            date_from="2024-01-01",
            date_to="2024-01-10",
            session=fake_db,
        )
    monkeypatch.delenv("STATS_USE_SQL", raising=False)
