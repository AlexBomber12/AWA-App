import asyncio
from typing import Any

from awa_common.http_client import AsyncHTTPClient
from awa_common.settings import settings as SETTINGS

BASE = "https://api.helium10.com/financials/fba-fees/{}"
H10_KEY = SETTINGS.HELIUM10_KEY or ""
_HTTP_CLIENT: AsyncHTTPClient | None = None
_HTTP_LOCK = asyncio.Lock()


async def _get_http_client() -> AsyncHTTPClient:
    global _HTTP_CLIENT
    client = _HTTP_CLIENT
    if client is not None:
        return client
    async with _HTTP_LOCK:
        if _HTTP_CLIENT is None:
            _HTTP_CLIENT = AsyncHTTPClient(integration="helium10")
        return _HTTP_CLIENT


async def close_http_client() -> None:
    global _HTTP_CLIENT
    client = _HTTP_CLIENT
    if client is None:
        return
    _HTTP_CLIENT = None
    await client.aclose()


async def fetch_fees(asin: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {H10_KEY}"} if H10_KEY else {}
    client = await _get_http_client()
    data = await client.get_json(BASE.format(asin), headers=headers)
    return {
        "asin": asin,
        "fulfil_fee": float(data.get("fulfillmentFee", 0)),
        "referral_fee": float(data.get("referralFee", 0)),
        "storage_fee": float(data.get("storageFee", 0)),
        "currency": data.get("currency", "EUR"),
    }
