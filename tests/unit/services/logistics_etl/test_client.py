""""""

from __future__ import annotations

import io
import sys
from datetime import datetime
from types import SimpleNamespace
from urllib.parse import urlparse

import httpx
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
            b"carrier,origin,dest,service,eur_per_kg,effective_from,effective_to\n"
            b"DHL,DE,FR,EXPRESS,1.25,2024-01-01,\n"
        )
        return raw, {"content_type": "text/csv"}

    monkeypatch.setattr(client, "_download_with_retries", fake_download)
    snapshots = await client.fetch_sources()
    assert len(snapshots) == 1
    entry = snapshots[0]
    rows = entry["rows"]
    assert rows[0]["carrier"] == "DHL"
    assert rows[0]["eur_per_kg"] == pytest.approx(1.25)
    assert rows[0]["effective_to"] is None
    monkeypatch.delenv("LOGISTICS_SOURCES", raising=False)


@pytest.mark.asyncio
async def test_download_with_retries_http_recovers(monkeypatch):
    attempts = {"count": 0}

    async def fake_download(url, timeout_s):
        attempts["count"] += 1
        if attempts["count"] == 1:
            request = httpx.Request("GET", url)
            response = httpx.Response(503, request=request)
            raise httpx.HTTPStatusError("server error", request=request, response=response)
        return b"ok", {}

    monkeypatch.setattr(client, "_download_http", fake_download)
    data, meta = await client._download_with_retries(
        "http://logistics.example/rates.csv", timeout_s=1, retries=2
    )
    assert data == b"ok"
    assert meta == {}
    assert attempts["count"] == 2


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
        return payload, {
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }

    monkeypatch.setattr(client, "_download_with_retries", fake_download)
    snapshots = await client.fetch_sources()
    assert snapshots[0]["rows"][0]["carrier"] == "Maersk"
    assert snapshots[0]["rows"][0]["eur_per_kg"] == pytest.approx(0.85)
    monkeypatch.delenv("LOGISTICS_SOURCES", raising=False)
