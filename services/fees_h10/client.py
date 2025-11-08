from typing import Any

from awa_common.settings import settings as SETTINGS
from services.etl import http_client

BASE = "https://api.helium10.com/financials/fba-fees/{}"
H10_KEY = SETTINGS.HELIUM10_KEY or ""


async def fetch_fees(asin: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {H10_KEY}"} if H10_KEY else {}
    data = await http_client.request_json(
        "GET",
        BASE.format(asin),
        headers=headers,
        source="helium10_client",
    )
    return {
        "asin": asin,
        "fulfil_fee": float(data.get("fulfillmentFee", 0)),
        "referral_fee": float(data.get("referralFee", 0)),
        "storage_fee": float(data.get("storageFee", 0)),
        "currency": data.get("currency", "EUR"),
    }
