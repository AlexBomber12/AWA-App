""""""

from __future__ import annotations

import io
import sys
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest

from services.logistics_etl import client


def test_detect_format_prefers_csv_extension():
    payload = b"carrier,origin,dest\n"
    assert client._detect_format(payload, "rates.csv") == "csv"
    assert client._detect_format(payload, "text/csv") == "csv"


@pytest.mark.asyncio
async def test_fetch_sources_csv_normalizes_rows(monkeypatch):
    monkeypatch.setenv("LOGISTICS_SOURCES", "http://example.com/rates.csv")

    async def fake_download(uri, timeout_s, retries):
        raw = (
            b"carrier,origin,dest,service,eur_per_kg,effective_from,effective_to\nDHL,DE,FR,EXPRESS,1.25,2024-01-01,\n"
        )
        return raw, {"content_type": "text/csv"}

    monkeypatch.setattr(client, "_download_with_retries", fake_download)
    snapshots = await client.fetch_sources()
    assert len(snapshots) == 1
    entry = snapshots[0]
    rows = entry["rows"]
    assert rows[0]["carrier"] == "DHL"
    assert rows[0]["eur_per_kg"] == Decimal("1.25")
    assert rows[0]["valid_to"] is None
    monkeypatch.delenv("LOGISTICS_SOURCES", raising=False)


@pytest.mark.asyncio
async def test_download_with_retries_http_recovers(monkeypatch):
    calls: dict[str, object] = {}

    async def fake_download(url, timeout_s=None, retries=None):
        calls["url"] = url
        calls["timeout_s"] = timeout_s
        calls["retries"] = retries
        return b"ok", {}

    monkeypatch.setattr(client, "_download_http", fake_download)
    data, meta = await client._download_with_retries("http://logistics.example/rates.csv", timeout_s=1, retries=2)
    assert data == b"ok"
    assert meta == {}
    assert calls["timeout_s"] == 1
    assert int(calls["retries"]) >= 2


@pytest.mark.asyncio
async def test_download_ftp_returns_metadata(monkeypatch):
    class DummyFTP:
        def __init__(self):
            self.buffer = io.BytesIO()

        def connect(self, host, port, timeout):
            assert host == "ftp.example.com"
            assert port == 21

        def login(self, username, password):
            assert username == "user"
            assert password == "pass"

        def retrbinary(self, cmd, callback):
            assert cmd == "RETR path/to/file.csv"
            callback(b"carrier,origin,dest\n")

        def sendcmd(self, cmd):
            assert cmd == "MDTM path/to/file.csv"
            return "213 20240101000000"

        def quit(self):
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.quit()

    async def fake_run_sync(func, limiter=None):
        return func()

    import ftplib

    monkeypatch.setattr(client.anyio.to_thread, "run_sync", fake_run_sync)
    monkeypatch.setattr(ftplib, "FTP", DummyFTP)
    parsed = urlparse("ftp://user:pass@ftp.example.com/path/to/file.csv")
    raw, meta = await client._download_ftp(parsed, timeout_s=5)
    assert raw.startswith(b"carrier")
    assert meta["seqno"] == "20240101000000"


@pytest.mark.asyncio
async def test_download_s3_uses_etag_when_version_missing(monkeypatch):
    class DummyBody(io.BytesIO):
        def __init__(self):
            super().__init__(b"carrier,origin,dest\n")

    class DummyS3Client:
        def get_object(self, Bucket, Key, **extra):
            assert Bucket == "rates-bucket"
            assert Key == "daily/rates.csv"
            return {
                "Body": DummyBody(),
                "ETag": '"etag123"',
                "ContentType": "text/csv",
                "LastModified": datetime(2024, 1, 1),
            }

    async def fake_run_sync(func, limiter=None):
        return func()

    dummy_boto3 = SimpleNamespace(client=lambda *_a, **_k: DummyS3Client())
    dummy_exceptions = SimpleNamespace(BotoCoreError=Exception, ClientError=Exception)

    monkeypatch.setitem(sys.modules, "boto3", dummy_boto3)
    monkeypatch.setitem(sys.modules, "botocore.exceptions", dummy_exceptions)
    monkeypatch.setattr(client.anyio.to_thread, "run_sync", fake_run_sync)

    parsed = urlparse("s3://rates-bucket/daily/rates.csv")
    raw, meta = await client._download_s3(parsed, timeout_s=5)
    assert raw.startswith(b"carrier")
    assert meta["seqno"] == "etag123"
    assert meta["etag"] == "etag123"


@pytest.mark.asyncio
async def test_fetch_sources_excel(monkeypatch):
    openpyxl = pytest.importorskip("openpyxl")
    monkeypatch.setenv("LOGISTICS_SOURCES", "s3://bucket/rates.xlsx")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(
        [
            "carrier",
            "origin",
            "dest",
            "service",
            "eur_per_kg",
            "effective_from",
            "effective_to",
        ]
    )
    ws.append(["Maersk", "CN", "NL", "Ocean", 0.85, "2024-02-01", "2024-04-01"])
    buffer = io.BytesIO()
    wb.save(buffer)
    payload = buffer.getvalue()

    async def fake_download(uri, timeout_s, retries):
        return payload, {"content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}

    monkeypatch.setattr(client, "_download_with_retries", fake_download)
    snapshots = await client.fetch_sources()
    assert snapshots[0]["rows"][0]["carrier"] == "Maersk"
    assert snapshots[0]["rows"][0]["eur_per_kg"] == Decimal("0.85")
    monkeypatch.delenv("LOGISTICS_SOURCES", raising=False)


@pytest.mark.asyncio
async def test_fetch_sources_unsupported_format(monkeypatch):
    monkeypatch.setenv("LOGISTICS_SOURCES", "http://example.com/file.bin")

    async def fake_download(*_args, **_kwargs):
        return b"raw", {"content_type": "application/octet-stream"}

    def raise_unsupported(*_args, **_kwargs):
        raise client.UnsupportedFileFormatError("bad format")

    monkeypatch.setattr(client, "_download_with_retries", fake_download)
    monkeypatch.setattr(client, "_parse_rows", raise_unsupported)

    with pytest.raises(client.UnsupportedFileFormatError):
        await client.fetch_sources()

    monkeypatch.delenv("LOGISTICS_SOURCES", raising=False)


@pytest.mark.asyncio
async def test_ensure_http_client_respects_settings(monkeypatch):
    from services.logistics_etl import client as client_module

    existing = client_module._HTTP_CLIENT
    if existing is not None:
        await existing.aclose()
    client_module._HTTP_CLIENT = None
    client_module._HTTP_CLIENT_CONFIG = None

    config = SimpleNamespace(
        LOGISTICS_TIMEOUT_S=9.5,
        LOGISTICS_RETRIES=4,
        ETL_RETRY_ATTEMPTS=2,
        HTTP_MAX_RETRIES=1,
    )
    monkeypatch.setattr(client_module, "Settings", lambda: config, raising=False)

    http_client = await client_module._ensure_http_client()
    try:
        assert http_client.integration == "logistics_etl"
        assert http_client._total_timeout_s == 9.5  # type: ignore[attr-defined]
        assert http_client._max_retries == 4  # type: ignore[attr-defined]
    finally:
        await http_client.aclose()
        client_module._HTTP_CLIENT = None
        client_module._HTTP_CLIENT_CONFIG = None


@pytest.mark.asyncio
async def test_download_http_falls_back_to_content(monkeypatch):
    class DummyResponse:
        def __init__(self) -> None:
            self.headers = {"content-type": "text/csv"}
            self.content = b"carrier,origin\n"
            self.closed = False
            self.status_code = 200

        def raise_for_status(self) -> None:
            return None

        async def aiter_bytes(self, _chunk_size: int):
            yield self.content

        async def aread(self):
            return self.content

        async def aclose(self):
            self.closed = True

    class DummyClient:
        async def request(self, *_args, **_kwargs):
            return DummyResponse()

        async def aclose(self):
            return None

    async def fake_ensure_http_client(**_kwargs):
        return DummyClient()

    monkeypatch.setattr(client, "_ensure_http_client", fake_ensure_http_client)

    body, meta = await client._download_http("https://example.com/data.csv")
    assert body.startswith(b"carrier")
    assert meta["content_type"] == "text/csv"
