import pytest

from services.worker.repricer.app import main


class StubResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class StubSession:
    def __init__(self, rows):
        self.rows = rows

    async def execute(self, query):
        return StubResult(self.rows)


@pytest.mark.asyncio
async def test_full(monkeypatch):
    rows = [("A1", 10, 2)]
    sess = StubSession(rows)
    res = await main.full(sess)
    assert res[0].asin == "A1"
    assert res[0].new_price >= 12
