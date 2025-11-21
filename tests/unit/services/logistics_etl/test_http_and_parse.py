from __future__ import annotations

import builtins
from decimal import Decimal
from pathlib import Path

import pytest

from services.logistics_etl import client


@pytest.mark.asyncio
async def test_download_with_retries_success(monkeypatch) -> None:
    payload = b"country,rate\nDE,1.5\n"
    meta = {"content_type": "text/csv"}
    calls = {"count": 0}

    async def _fake_http(url: str, timeout_s: int, retries=None):
        calls["count"] += 1
        return payload, meta

    monkeypatch.setattr(client, "_download_http", _fake_http, raising=False)
    result = await client._download_with_retries("https://example.com/rates.csv", timeout_s=5, retries=1)
    assert result == (payload, meta)
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_download_http_parses_metadata(monkeypatch) -> None:
    class _DummyResponse:
        def __init__(self):
            self.headers = {
                "content-type": "text/csv",
                "etag": '"abc123"',
                "last-modified": "Mon, 01 Jan 2024 00:00:00 GMT",
                "x-amz-version-id": '"v2"',
            }

        async def aread(self) -> bytes:
            return b"sku,rate\n"

        def close(self) -> None:
            return None

    class _DummyClient:
        async def request(self, method: str, url: str, **kwargs):
            self.method = method
            self.url = url
            return _DummyResponse()

    async def _fake_client(*args, **kwargs):
        return _DummyClient()

    monkeypatch.setattr(client, "_ensure_http_client", _fake_client, raising=False)
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
    assert rows[0]["eur_per_kg"] == Decimal("1.25")


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
