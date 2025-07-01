import types
import sys
import os
import asyncio
from typing import cast
from types import ModuleType


class FakePool:
    def __init__(self):
        self.log = []

    async def fetch(self, query):
        return [{"offer_id": 1, "asin": "ASIN1", "target_min": 10}]

    async def execute(self, query, offer_id, price):
        self.log.append((offer_id, price))

    async def close(self):
        pass


class FakeListings:
    def __init__(self, credentials):
        self.calls = []

    def pricing(self, asin, price):
        self.calls.append((asin, price))


pool = FakePool()


async def fake_create_pool(dsn):
    return pool


class FakeSPModule:
    def __init__(self):
        self.instance = FakeListings(None)

    def Listings(self, credentials):
        return self.instance


sys.modules["asyncpg"] = cast(
    ModuleType, types.SimpleNamespace(create_pool=fake_create_pool)
)
fake_sp = FakeSPModule()
sys.modules["sp_api.api"] = cast(ModuleType, fake_sp)

from services.repricer import repricer


def test_main():
    os.environ["PG_DSN"] = "d"
    os.environ["SP_REFRESH_TOKEN"] = "t"
    os.environ["SP_CLIENT_ID"] = "i"
    os.environ["SP_CLIENT_SECRET"] = "s"
    asyncio.run(repricer.main())
    assert fake_sp.instance.calls == [("ASIN1", 10)]
    assert pool.log == [(1, 10)]
