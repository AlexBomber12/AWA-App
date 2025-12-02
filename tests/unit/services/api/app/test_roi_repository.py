from __future__ import annotations

import pytest

from services.api.app.repositories import roi as roi_repo


class DummyResult:
    def __init__(self, rows=None, scalar_rows=None):
        self._rows = rows or []
        self._scalar_rows = scalar_rows or []

    def mappings(self):
        return DummyMappings(self._rows)

    def scalars(self):
        return DummyScalars(self._scalar_rows)


class DummyMappings:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class DummyScalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class DummyTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummySession:
    def __init__(self, rows=None, scalar_rows=None):
        self.rows = rows or []
        self.scalar_rows = scalar_rows or []
        self.executed = []
        self.begin_called = 0

    async def execute(self, stmt, params):
        self.executed.append((str(stmt), dict(params or {})))
        return DummyResult(self.rows, self.scalar_rows)

    def begin(self):
        self.begin_called += 1
        return DummyTransaction()


@pytest.mark.asyncio
async def test_fetch_pending_rows_includes_filters(monkeypatch):
    monkeypatch.setattr(roi_repo, "get_roi_view_name", lambda: "v_roi_full")
    session = DummySession(rows=[{"asin": "A1"}])
    rows = await roi_repo.fetch_pending_rows(session, roi_min=10, vendor=42, category="Beauty")
    assert rows[0]["asin"] == "A1"
    sql, params = session.executed[0]
    assert "vendor_prices" in sql and "vendor_id = :vendor" in sql
    assert params["vendor"] == 42
    assert params["category"] == "Beauty"


@pytest.mark.asyncio
async def test_bulk_approve_returns_deduplicated_ids(monkeypatch):
    session = DummySession(scalar_rows=[101, 202])
    ids = await roi_repo.bulk_approve(session, ["A1", "A1", "A2"], approved_by="ops@example.com")
    assert ids == ["101", "202"]
    assert session.begin_called == 1
    sql, params = session.executed[0]
    assert "UPDATE products" in sql
    assert params["asins"] == ("A1", "A2")


def test_roi_listing_sql_has_stable_ordering(monkeypatch):
    monkeypatch.setattr(roi_repo, "quote_identifier", lambda name: name)
    roi_repo._roi_listing_sql.cache_clear()
    stmt = roi_repo._roi_listing_sql(
        "roi_view",
        include_vendor=False,
        include_category=True,
        include_search=True,
        include_roi_max=True,
        sort_key="roi_pct_desc",
    )
    sql = str(stmt)
    assert "ORDER BY vf.roi_pct DESC NULLS LAST, p.asin ASC" in sql
    assert "LIMIT :limit OFFSET :offset" in sql
    assert "vendor_prices" in sql
    assert "JOIN LATERAL" in sql


def test_roi_listing_sql_uses_vendor_filter(monkeypatch):
    monkeypatch.setattr(roi_repo, "quote_identifier", lambda name: name)
    roi_repo._roi_listing_sql.cache_clear()
    stmt = roi_repo._roi_listing_sql(
        "roi_view",
        include_vendor=True,
        include_category=False,
        include_search=False,
        include_roi_max=False,
        sort_key="margin_desc",
    )
    sql = str(stmt)
    assert "vendor_id = :vendor" in sql
    assert "vf.roi_pct >= :roi_min" in sql
    assert "NULLS LAST" in sql
