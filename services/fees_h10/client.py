import asyncio
from typing import Any

from awa_common.http_client import AsyncHTTPClient
from awa_common.settings import settings as SETTINGS

BASE_PATH = "/financials/fba-fees/{}"
H10_KEY: str | None = None
_HTTP_CLIENT: AsyncHTTPClient | None = None
_HTTP_CLIENT_CONFIG: tuple[str, float, int] | None = None
_HTTP_LOCK = asyncio.Lock()


def _helium_base_url() -> str:
    etl_cfg = getattr(SETTINGS, "etl", None)
    base = getattr(etl_cfg, "helium10_base_url", None) or getattr(SETTINGS, "HELIUM10_BASE_URL", "")
    return (base or "https://api.helium10.com").rstrip("/")


def _helium_timeout_s() -> float:
    etl_cfg = getattr(SETTINGS, "etl", None)
    return float(getattr(etl_cfg, "helium10_timeout_s", getattr(SETTINGS, "HELIUM10_TIMEOUT_S", 60.0)))


def _helium_max_retries() -> int:
    etl_cfg = getattr(SETTINGS, "etl", None)
    return max(1, int(getattr(etl_cfg, "helium10_max_retries", getattr(SETTINGS, "HELIUM10_MAX_RETRIES", 5))))


def _helium_key() -> str:
    etl_cfg = getattr(SETTINGS, "etl", None)
    manual = globals().get("H10_KEY", None)
    return (
        (manual if manual not in (None, "") else None)
        or getattr(etl_cfg, "helium10_key", None)
        or getattr(SETTINGS, "HELIUM10_KEY", "")
        or ""
    ).strip()


BASE = f"{_helium_base_url()}{BASE_PATH}"


def build_fee_url(asin: str) -> str:
    """Return the full Helium10 fee URL for the given ASIN."""

    return f"{_helium_base_url()}{BASE_PATH.format(asin)}"


async def _get_http_client() -> AsyncHTTPClient:
    global _HTTP_CLIENT, _HTTP_CLIENT_CONFIG
    client = _HTTP_CLIENT
    desired = (_helium_base_url(), _helium_timeout_s(), _helium_max_retries())
    if client is not None:
        if _HTTP_CLIENT_CONFIG == desired or not hasattr(client, "aclose"):
            _HTTP_CLIENT_CONFIG = desired
            return client
        await client.aclose()
    async with _HTTP_LOCK:
        client = _HTTP_CLIENT
        if client is not None:
            if _HTTP_CLIENT_CONFIG == desired or not hasattr(client, "aclose"):
                _HTTP_CLIENT_CONFIG = desired
                return client
            await client.aclose()
        _HTTP_CLIENT = AsyncHTTPClient(
            integration="helium10",
            base_url=desired[0],
            total_timeout_s=desired[1],
            max_retries=desired[2],
        )
        _HTTP_CLIENT_CONFIG = desired
        return _HTTP_CLIENT


async def close_http_client() -> None:
    global _HTTP_CLIENT
    client = _HTTP_CLIENT
    if client is None:
        return
    _HTTP_CLIENT = None
    await client.aclose()


async def fetch_fees(asin: str) -> dict[str, Any]:
    key = _helium_key()
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    client = await _get_http_client()
    data = await client.get_json(
        BASE_PATH.format(asin),
        headers=headers,
        timeout=_helium_timeout_s(),
    )
    return {
        "asin": asin,
        "fulfil_fee": float(data.get("fulfillmentFee", 0)),
        "referral_fee": float(data.get("referralFee", 0)),
        "storage_fee": float(data.get("storageFee", 0)),
        "currency": data.get("currency", "EUR"),
    }
