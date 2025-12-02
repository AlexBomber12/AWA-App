import httpx
import pytest

from services.llm_server import provider_client
from services.llm_server.errors import (
    LLMProviderClientError,
    LLMProviderTimeoutError,
    LLMProviderTransportError,
)
from services.llm_server.provider_client import LLMProviderHTTPClient, ProviderConfig


def _patch_metrics(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[tuple]]:
    calls = {"requests": [], "latency": [], "timeouts": []}
    monkeypatch.setattr(
        provider_client,
        "record_llm_provider_request",
        lambda provider, operation, outcome: calls["requests"].append((provider, operation, outcome)),
    )
    monkeypatch.setattr(
        provider_client,
        "observe_llm_provider_latency",
        lambda provider, operation, duration: calls["latency"].append((provider, operation, duration)),
    )
    monkeypatch.setattr(
        provider_client,
        "record_llm_provider_timeout",
        lambda provider, operation: calls["timeouts"].append((provider, operation)),
    )
    return calls


def _client(handler, *, max_retries: int = 1, retry_statuses: tuple[int, ...] | None = None) -> LLMProviderHTTPClient:
    return LLMProviderHTTPClient(
        config=ProviderConfig(name="local", base_url="https://example.com", api_key=None, integration="test"),
        request_timeout_s=0.5,
        max_retries=max_retries,
        backoff_base_s=0.0,
        backoff_max_s=0.0,
        retry_status_codes=retry_statuses,
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.anyio
async def test_provider_client_success(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]}, request=request)

    client = _client(handler)
    payload = await client.chat_completion({"model": "m", "messages": []}, operation="classify_email")
    assert payload["choices"][0]["message"]["content"] == "{}"
    assert ("local", "classify_email", "success") in events["requests"]
    assert events["latency"]
    assert events["timeouts"] == []


@pytest.mark.anyio
async def test_provider_client_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    client = _client(handler)
    with pytest.raises(LLMProviderTimeoutError):
        await client.chat_completion({"model": "m", "messages": []}, operation="chat_completion")
    assert ("local", "chat_completion", "timeout") in events["requests"]
    assert ("local", "chat_completion") in events["timeouts"]


@pytest.mark.anyio
async def test_provider_client_client_error(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "bad"}, request=request)

    client = _client(handler)
    with pytest.raises(LLMProviderClientError):
        await client.chat_completion({"model": "m", "messages": []}, operation="parse_price_list")
    assert ("local", "parse_price_list", "client_error") in events["requests"]


@pytest.mark.anyio
async def test_provider_client_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(500, request=request)
        return httpx.Response(200, json={"ok": True}, request=request)

    client = _client(handler, max_retries=2, retry_statuses=(500,))
    payload = await client.chat_completion({"model": "m", "messages": []}, operation="classify_email")
    assert payload == {"ok": True}
    assert attempts["count"] == 2
    assert ("local", "classify_email", "success") in events["requests"]


@pytest.mark.anyio
async def test_provider_client_transport_error(monkeypatch: pytest.MonkeyPatch) -> None:
    events = _patch_metrics(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    client = _client(handler)
    with pytest.raises(LLMProviderTransportError):
        await client.chat_completion({"model": "m", "messages": []}, operation="chat_completion")
    assert ("local", "chat_completion", "transport_error") in events["requests"]
