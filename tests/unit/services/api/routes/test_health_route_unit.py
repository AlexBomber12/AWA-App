import datetime

import pytest

from services.api.routes import health
from tests.unit.conftest import _StubResult


@pytest.mark.asyncio
async def test_health_ok(fake_db_session):
    now = datetime.datetime.utcnow()
    session = fake_db_session(_StubResult(scalar=now))
    response = await health.health(session=session)
    assert response.status_code == 200
    assert response.body and b"ok" in response.body


@pytest.mark.asyncio
async def test_health_clock_skew(fake_db_session):
    old = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    session = fake_db_session(_StubResult(scalar=old))
    response = await health.health(session=session)
    assert response.status_code == 503
    assert b"clock_skew" in response.body
