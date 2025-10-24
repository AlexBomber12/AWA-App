from __future__ import annotations

from typing import Any


class Listings:
    def __init__(self, credentials: dict[str, Any]) -> None:
        pass

    def pricing(self, asin: str, price: float) -> None:
        pass


class SellingPartnerAPI:
    def get_my_fees_estimate_for_sku(self, seller_sku: str) -> dict[str, Any]:
        return {}
