from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from awa_common import http_client
from awa_common.http_client import AsyncHTTPClient, HTTPClient, RetryableStatusError, _RetryWait


class DummyLogger:
    def __init__(self) -> None:
        self.records: dict[str, list[tuple[str, dict[str, Any]]]] = {
            "debug": [],
            "info": [],
            "warning": [],
        }

    def debug(self, event: str, **kwargs: Any) -> None:
        self.records["debug"].append((event, kwargs))

    def info(self, event: str, **kwargs: Any) -> None:
        self.records["info"].append((event, kwargs))

    def warning(self, event: str, **kwargs: Any) -> None:
        self.records["warning"].append((event, kwargs))

    def bind(self, **bound: Any):
        parent = self

        class _Bound:
            def debug(self, event: str, **kwargs: Any) -> None:
                parent.records["debug"].append((event, {**bound, **kwargs}))

            def info(self, event: str, **kwargs: Any) -> None:
                parent.records["info"].append((event, {**bound, **kwargs}))

            def warning(self, event: str, **kwargs: Any) -> None:
                parent.records["warning"].append((event, {**bound, **kwargs}))

        return _Bound()


def _patch_metrics(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[tuple]]:
    calls = {"requests": [], "latency": [], "retries": []}
    monkeypatch.setattr(
        http_client,
        "record_external_http_request",
        lambda integration, method, outcome: calls["requests"].append((integration, method, outcome)),
    )
    monkeypatch.setattr(
        http_client,
        "observe_external_http_latency",
        lambda integration, method, duration: calls["latency"].append((integration, method, duration)),
    )
    monkeypatch.setattr(
        http_client,
        "record_external_http_retry",
        lambda integration, method, reason: calls["retries"].append((integration, method, reason)),
    )
    return calls


def test_http_client_get_json_success(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)
    dummy_logger = DummyLogger()
    monkeypatch.setattr(http_client, "logger", dummy_logger)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://example.com/data")
        return httpx.Response(200, json={"ok": True}, request=request)

    client = HTTPClient(integration="unit", transport=httpx.MockTransport(handler))
    payload = client.get_json("https://example.com/data")
    assert payload == {"ok": True}
    assert ("unit", "GET", "success") in events["requests"]
    assert dummy_logger.records["info"]


def test_http_client_retries_on_5xx(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)
    dummy_logger = DummyLogger()
    monkeypatch.setattr(http_client, "logger", dummy_logger)
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 2:
            return httpx.Response(503, headers={"Retry-After": "0"}, request=request)
        return httpx.Response(200, json={"ok": True}, request=request)

    client = HTTPClient(integration="unit", transport=httpx.MockTransport(handler))
    result = client.get_json("https://example.com/api")
    assert result == {"ok": True}
    assert attempts["count"] == 2
    assert events["retries"]
    assert any(rec[2] == "503" for rec in events["retries"])


def test_http_client_retry_exhaustion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(http_client.settings, "HTTP_MAX_RETRIES", 2, raising=False)
    monkeypatch.setattr(http_client.settings, "HTTP_TOTAL_TIMEOUT_S", 1.0, raising=False)
    events = _patch_metrics(monkeypatch)
    dummy_logger = DummyLogger()
    monkeypatch.setattr(http_client, "logger", dummy_logger)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, request=request)

    client = HTTPClient(integration="unit", transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        client.get("https://example.com/fail")
    assert any(outcome[2] == "retry_exhausted" for outcome in events["requests"])
    assert dummy_logger.records["warning"]


def test_http_client_timeout_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(http_client.settings, "HTTP_MAX_RETRIES", 2, raising=False)
    events = _patch_metrics(monkeypatch)
    dummy_logger = DummyLogger()
    monkeypatch.setattr(http_client, "logger", dummy_logger)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("boom", request=request)

    client = HTTPClient(integration="unit", transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.ConnectTimeout):
        client.get("https://example.com/timeout")
    assert ("unit", "GET", "retry_exhausted") in events["requests"]
    assert dummy_logger.records["warning"]


def test_http_client_download_to_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)
    dummy_logger = DummyLogger()
    monkeypatch.setattr(http_client, "logger", dummy_logger)
    content = b"hello-world"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=content, request=request)

    client = HTTPClient(integration="unit", transport=httpx.MockTransport(handler))
    dest = tmp_path / "payload.bin"
    path = client.download_to_file("https://example.com/blob", dest_path=dest)
    assert path.read_bytes() == content
    assert ("unit", "GET", "success") in events["requests"]


def test_retry_wait_prefers_retry_after() -> None:
    wait = _RetryWait(multiplier=0.1, max=10, jitter=0.0)
    request = httpx.Request("GET", "https://example.com")
    response = httpx.Response(503, headers={"Retry-After": "2"}, request=request)
    exc = RetryableStatusError("boom", request=request, response=response, retry_after=5.0)
    state = SimpleNamespace(
        outcome=SimpleNamespace(failed=True, exception=lambda: exc),
        attempt_number=1,
        next_action=None,
    )
    assert wait(state) == pytest.approx(5.0)


def test_http_client_allows_status(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(304, request=request, headers={"ETag": "v1"})

    client = HTTPClient(integration="unit", transport=httpx.MockTransport(handler))
    resp = client.request("GET", "https://example.com/resource", allowed_statuses={304})
    assert resp.status_code == 304
    resp.close()
    assert ("unit", "GET", "success") in events["requests"]


def test_http_client_download_calls_on_chunk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)
    content = b"onetwothree"
    seen = {"bytes": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=content, request=request)

    def on_chunk(chunk: bytes) -> None:
        seen["bytes"] += len(chunk)

    client = HTTPClient(integration="unit", transport=httpx.MockTransport(handler))
    target = tmp_path / "payload.bin"
    client.download_to_file("https://example.com/object", dest_path=target, chunk_size=4, on_chunk=on_chunk)
    assert seen["bytes"] == len(content)
    assert target.read_bytes() == content
    assert ("unit", "GET", "success") in events["requests"]


@pytest.mark.anyio
async def test_async_http_client_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(http_client.settings, "HTTP_MAX_RETRIES", 2, raising=False)
    dummy_logger = DummyLogger()
    monkeypatch.setattr(http_client, "logger", dummy_logger)
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 2:
            return httpx.Response(502, request=request)
        return httpx.Response(200, json={"ok": True}, request=request)

    client = AsyncHTTPClient(integration="unit", transport=httpx.MockTransport(handler))
    payload = await client.get_json("https://example.com/async")
    await client.aclose()
    assert payload == {"ok": True}
    assert attempts["count"] == 2


@pytest.mark.anyio
async def test_async_http_client_download(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)
    dummy_logger = DummyLogger()
    monkeypatch.setattr(http_client, "logger", dummy_logger)
    content = b"async-data"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=content, request=request)

    client = AsyncHTTPClient(integration="unit", transport=httpx.MockTransport(handler))
    dest = tmp_path / "async.bin"
    path = await client.download_to_file("https://example.com/async-blob", dest_path=dest)
    await client.aclose()
    assert path.read_bytes() == content
    assert ("unit", "GET", "success") in events["requests"]


@pytest.mark.anyio
async def test_async_http_client_allowed_status(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(304, request=request)

    client = AsyncHTTPClient(integration="unit", transport=httpx.MockTransport(handler))
    response = await client.request("GET", "https://example.com/cache", allowed_statuses={304})
    assert response.status_code == 304
    await response.aclose()
    await client.aclose()
    assert ("unit", "GET", "success") in events["requests"]


@pytest.mark.anyio
async def test_async_http_client_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(http_client.settings, "HTTP_MAX_RETRIES", 2, raising=False)
    events = _patch_metrics(monkeypatch)
    dummy_logger = DummyLogger()
    monkeypatch.setattr(http_client, "logger", dummy_logger)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    client = AsyncHTTPClient(integration="unit", transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.ReadTimeout):
        await client.get("https://example.com/slow")
    await client.aclose()
    assert ("unit", "GET", "retry_exhausted") in events["requests"]
    assert dummy_logger.records["warning"]
