from __future__ import annotations

import asyncio

import pytest
from httpx import MockTransport, Request, Response

from awa_common.http_client import AsyncHTTPClient, HTTPClient


def test_http_client_allows_status_success(tmp_path) -> None:
    def handler(request: Request) -> Response:
        return Response(202, request=request, content=b"ok")

    client = HTTPClient(
        integration="test",
        transport=MockTransport(handler),
        max_retries=1,
        total_timeout_s=1,
    )

    resp = client.get("https://example.com/ok", allowed_statuses={202})
    try:
        assert resp.status_code == 202
    finally:
        resp.close()


def test_http_client_download_calls_on_chunk(tmp_path) -> None:
    payload = b"hello world"

    def handler(request: Request) -> Response:
        return Response(200, request=request, content=payload)

    client = HTTPClient(
        integration="test",
        transport=MockTransport(handler),
        max_retries=1,
        total_timeout_s=1,
    )
    dest = tmp_path / "file.bin"
    chunks: list[bytes] = []

    client.download_to_file("https://example.com/file", dest_path=dest, on_chunk=chunks.append, chunk_size=4)

    assert b"".join(chunks) == payload
    assert dest.read_bytes() == payload


@pytest.mark.asyncio
async def test_async_http_client_allows_status_and_async_chunk(tmp_path) -> None:
    payload = b"abcd"

    def handler(request: Request) -> Response:
        status = 202 if "allow" in str(request.url) else 200
        return Response(status, request=request, content=payload)

    client = AsyncHTTPClient(
        integration="test",
        transport=MockTransport(handler),
        max_retries=1,
        total_timeout_s=1,
    )

    closed: dict[str, bool] = {}

    async def fake_aclose() -> None:
        closed["closed"] = True

    client._client.aclose = fake_aclose  # type: ignore[attr-defined]

    async with client as cli:
        resp = await cli.get("https://example.com/allow", allowed_statuses={202})
        assert resp.status_code == 202
        await cli._close_response(resp)

        dest = tmp_path / "async.bin"
        seen: list[bytes] = []

        async def on_chunk(data: bytes) -> None:
            await asyncio.sleep(0)  # exercise awaitable branch
            seen.append(data)

        await cli.download_to_file("https://example.com/download", dest_path=dest, on_chunk=on_chunk, chunk_size=2)

    assert closed.get("closed") is True
    assert b"".join(seen) == payload
    assert dest.read_bytes() == payload
