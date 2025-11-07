from __future__ import annotations

import builtins
from pathlib import Path
from typing import Any

import httpx
import pytest

from services.logistics_etl import client


@pytest.mark.asyncio
async def test_download_with_retries_success(monkeypatch) -> None:
    payload = b"country,rate\nDE,1.5\n"
    meta = {"content_type": "text/csv"}
    calls = {"count": 0}

    async def _fake_http(url: str, timeout_s: int):
        calls["count"] += 1
        return payload, meta

    monkeypatch.setattr(client, "_download_http", _fake_http)
    result = await client._download_with_retries("https://example.com/rates.csv", timeout_s=5, retries=1)
    assert result == (payload, meta)
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_download_with_retries_raises_on_429(monkeypatch) -> None:
    req = httpx.Request("GET", "https://example.com/rates.csv")
    resp = httpx.Response(429, request=req)

    async def _raise(*_args, **_kwargs):
        raise httpx.HTTPStatusError("too many", request=req, response=resp)

    monkeypatch.setattr(client, "_download_http", _raise)
    with pytest.raises(httpx.HTTPStatusError):
        await client._download_with_retries("https://example.com/rates.csv", timeout_s=5, retries=3)


@pytest.mark.asyncio
async def test_download_with_retries_retries_on_500(monkeypatch) -> None:
    req = httpx.Request("GET", "https://example.com/rates.csv")
    resp = httpx.Response(500, request=req)
    attempts = {"count": 0}
    sleeps: list[float] = []

    async def _fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    async def _flaky(url: str, timeout_s: int):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise httpx.HTTPStatusError("server error", request=req, response=resp)
        return b"ok", {}

    monkeypatch.setattr(client, "_download_http", _flaky)
    monkeypatch.setattr(client.asyncio, "sleep", _fake_sleep)

    payload, meta = await client._download_with_retries("https://example.com/rates.csv", timeout_s=5, retries=5)
    assert payload == b"ok"
    assert meta == {}
    assert attempts["count"] == 3
    assert sleeps, "backoff should be applied"


@pytest.mark.asyncio
async def test_download_with_retries_timeout(monkeypatch) -> None:
    async def _timeout(*_args, **_kwargs):
        raise httpx.TimeoutException("slow response")

    async def _sleep_stub(_delay: float) -> None:
        return None

    monkeypatch.setattr(client, "_download_http", _timeout)
    monkeypatch.setattr(client.asyncio, "sleep", _sleep_stub)

    with pytest.raises(httpx.TimeoutException):
        await client._download_with_retries("https://example.com/rates.csv", timeout_s=1, retries=1)


@pytest.mark.asyncio
async def test_download_http_parses_metadata(monkeypatch) -> None:
    class _DummyResponse:
        def __init__(self):
            self.status_code = 200
            self.headers = {
                "content-type": "text/csv",
                "etag": '"abc123"',
                "last-modified": "Mon, 01 Jan 2024 00:00:00 GMT",
                "x-amz-version-id": '"v2"',
            }
            self.content = b"sku,rate\n"

        def raise_for_status(self) -> None:
            return None

    class _DummyClient:
        def __init__(self, *args, **kwargs):
            self.called_with: dict[str, Any] = {}

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str):
            self.called_with["url"] = url
            return _DummyResponse()

    monkeypatch.setattr(client.httpx, "AsyncClient", _DummyClient)
    content, meta = await client._download_http("https://example.com/rates.csv", timeout_s=5)
    assert content.startswith(b"sku")
    assert meta["content_type"] == "text/csv"
    assert meta["etag"] == "abc123"
    assert meta["seqno"] == "v2"


def test_parse_rows_from_csv_fixture() -> None:
    fixture_path = Path(__file__).resolve().parents[3] / "fixtures" / "logistics_etl" / "rates_sample.csv"
    fixture = fixture_path.read_bytes()
    rows = client._parse_rows(
        "https://example.com/rates.csv",
        fixture,
        {"content_type": "text/csv"},
    )
    assert len(rows) == 3
    assert rows[0]["carrier"] == "DHL"
    assert rows[0]["eur_per_kg"] == pytest.approx(1.25)


def test_parse_rows_unsupported_format(monkeypatch) -> None:
    real_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "openpyxl":
            raise ImportError("missing openpyxl")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    with pytest.raises(client.UnsupportedExcelError):
        client._parse_rows(
            "s3://bucket/data.xlsx",
            b"\x00\x01",
            {"content_type": "application/vnd.ms-excel"},
        )


@pytest.mark.asyncio
async def test_fetch_rates_normalizes_values(monkeypatch) -> None:
    sample = b"carrier,eur_per_kg\nDHL,1.5\nUPS,invalid\n"

    async def _fake_download(url, timeout_s, retries):
        return sample, {}

    monkeypatch.setattr(client, "_download_with_retries", _fake_download)
    monkeypatch.setenv("FREIGHT_API_URL", "https://example.com/rates.csv")
    rows = await client.fetch_rates()
    assert len(rows) == 2
    assert rows[0]["carrier"] == "DHL"
    assert rows[0]["eur_per_kg"] == pytest.approx(1.5)
    assert rows[1]["eur_per_kg"] == 0.0
