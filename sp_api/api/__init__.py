from __future__ import annotations

import atexit
from typing import Any

from awa_common.http_client import HTTPClient
from awa_common.settings import settings


class Listings:
    def __init__(self, credentials: dict[str, Any]) -> None:
        pass

    def pricing(self, asin: str, price: float) -> None:
        pass


class SellingPartnerAPI:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        transport: Any | None = None,
        **_: Any,
    ) -> None:
        resolved = base_url or settings.SP_API_BASE_URL
        self._client: HTTPClient | None = None
        if resolved:
            self._client = HTTPClient(integration="sp_api", base_url=resolved, transport=transport)
            atexit.register(self._client.close)

    def get_my_fees_estimate_for_sku(self, seller_sku: str) -> dict[str, Any]:
        if self._client is None:
            return {}
        response = self._client.post(
            "/products/pricing/fees",
            json={"seller_sku": seller_sku},
        )
        try:
            return response.json()
        finally:
            response.close()
