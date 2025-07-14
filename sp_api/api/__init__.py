from __future__ import annotations

from typing import Any, Dict


class Listings:
    def __init__(self, credentials: Dict[str, Any]) -> None:
        pass

    def pricing(self, asin: str, price: float) -> None:
        pass


class SellingPartnerAPI:
    def get_my_fees_estimate_for_sku(self, seller_sku: str) -> Dict[str, Any]:
        return {}
