import os
from typing import Any

import httpx

BASE = "https://api.helium10.com/financials/fba-fees/{}"
H10_KEY = os.getenv("HELIUM10_KEY", "")


async def fetch_fees(asin: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {H10_KEY}"} if H10_KEY else {}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(BASE.format(asin), headers=headers)
        r.raise_for_status()
        data = r.json()
    return {
        "asin": asin,
        "fulfil_fee": float(data.get("fulfillmentFee", 0)),
        "referral_fee": float(data.get("referralFee", 0)),
        "storage_fee": float(data.get("storageFee", 0)),
        "currency": data.get("currency", "EUR"),
    }
