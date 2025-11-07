import os
from typing import Any

from services.etl import http_client

BASE = "https://api.helium10.com/financials/fba-fees/{}"
H10_KEY = os.getenv("HELIUM10_KEY", "")


def _auth_headers() -> dict[str, str]:
    key = os.getenv("HELIUM10_KEY", H10_KEY) or ""
    return {"Authorization": f"Bearer {key}"} if key else {}


async def fetch_fees(asin: str) -> dict[str, Any]:
    headers = _auth_headers()
    response = await http_client.request("GET", BASE.format(asin), headers=headers)
    data = response.json()
    return {
        "asin": asin,
        "fulfil_fee": float(data.get("fulfillmentFee", 0)),
        "referral_fee": float(data.get("referralFee", 0)),
        "storage_fee": float(data.get("storageFee", 0)),
        "currency": data.get("currency", "EUR"),
    }
