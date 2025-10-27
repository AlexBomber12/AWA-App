import pytest

from services.api.routes import repository
from tests.unit.conftest import _StubResult


@pytest.mark.asyncio
async def test_fetch_roi_rows_returns_mapping(fake_db_session):
    rows = [{"asin": "A1", "roi_pct": 0.2}]
    session = fake_db_session(_StubResult(mappings=rows))
    result = await repository.fetch_roi_rows(session, 10, vendor=None, category=None)
    assert result == rows
    stmt, params = session.executed[0]
    assert "SELECT" in str(stmt)
    assert params["roi_min"] == 10


@pytest.mark.asyncio
async def test_bulk_approve_commits(fake_db_session):
    session = fake_db_session(_StubResult(rowcount=3))
    count = await repository.bulk_approve(session, ["A1", "A2"])
    assert count == 3
    assert session.committed is True
    stmt, params = session.executed[0]
    assert "UPDATE products" in str(stmt)
    assert params["asins"] == ("A1", "A2")


@pytest.mark.asyncio
async def test_bulk_approve_no_asins(fake_db_session):
    session = fake_db_session()
    count = await repository.bulk_approve(session, [])
    assert count == 0
    assert session.executed == []
