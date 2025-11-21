import types

import pytest

import awa_common.llm as llm


def test_timeout_seconds_handles_invalid(monkeypatch):
    assert llm._timeout_seconds(3.5) == 3.5


def test_timeout_seconds_uses_settings(monkeypatch):
    fallback_settings = types.SimpleNamespace(llm=types.SimpleNamespace(request_timeout_s=12.5))
    monkeypatch.setattr(llm, "_settings", fallback_settings)
    assert llm._timeout_seconds(None) == 12.5


@pytest.mark.asyncio
async def test_generate_stub_provider_returns_prefix():
    result = await llm._generate_with_provider("stub", "hello world", temperature=0.1, max_tokens=32, timeout=1.0)
    assert result.startswith("[stub]")


@pytest.mark.asyncio
async def test_generate_local_provider_uses_httpx(monkeypatch):
    calls = {}

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post_json(self, url, json, headers=None, timeout=None):
            calls["url"] = url
            calls["json"] = json
            calls["headers"] = headers
            calls["timeout"] = timeout
            return {"completion": "success"}

    monkeypatch.setattr(llm, "_build_http_client", lambda timeout, integration: DummyClient())
    result = await llm._generate_with_provider("local", "prompt text", temperature=0.5, max_tokens=64, timeout=2.0)
    assert result == "success"
    assert "prompt text" in calls["json"]["prompt"]


@pytest.mark.asyncio
async def test_generate_lan_provider_calls_remote(monkeypatch):
    recorded = {}

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post_json(self, url, json, headers=None, timeout=None):
            recorded["url"] = url
            recorded["headers"] = headers
            recorded["json"] = json
            recorded["timeout"] = timeout
            return {"choices": [{"message": {"content": "lan response"}}]}

    monkeypatch.setattr(llm, "_build_http_client", lambda timeout, integration: DummyClient())
    result = await llm._generate_with_provider("lan", "lan prompt", temperature=0.7, max_tokens=32, timeout=1.5)
    assert result == "lan response"
    assert "lan prompt" in recorded["json"]["messages"][0]["content"]


@pytest.mark.asyncio
async def test_generate_openai_provider_wraps_errors(monkeypatch):
    class DummyModule:
        class ChatCompletion:
            @staticmethod
            async def acreate(*_args, **_kwargs):
                raise RuntimeError("boom")

    monkeypatch.setattr(llm.importlib, "import_module", lambda name: DummyModule)

    with pytest.raises(RuntimeError) as excinfo:
        await llm._generate_with_provider("openai", "prompt", temperature=0.2, max_tokens=16, timeout=1.0)
    assert "openai provider call failed" in str(excinfo.value)


@pytest.mark.asyncio
async def test_generate_fallback_tries_multiple_providers(monkeypatch):
    attempts = []

    async def fake_generate(provider, *args, **kwargs):
        attempts.append(provider)
        if provider != "stub":
            raise RuntimeError("fail")
        return "[stub] done"

    monkeypatch.setattr(llm, "_generate_with_provider", fake_generate)
    result = await llm.generate("hello world", provider="lan", timeout=1.0)
    assert result == "[stub] done"
    assert attempts[0] == "lan"
    assert "stub" in attempts


def test_build_http_client_uses_timeout(monkeypatch):
    captured: dict[str, object] = {}

    class DummyClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(llm, "AsyncHTTPClient", DummyClient)
    client = llm._build_http_client(2.5, "demo")
    assert isinstance(client, DummyClient)
    assert captured["integration"] == "demo"
    assert captured["total_timeout_s"] == 2.5
    assert captured["max_retries"] == 1


@pytest.mark.asyncio
async def test_local_llm_uses_http_client(monkeypatch):
    calls: dict[str, object] = {}

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            calls["closed"] = True

        async def post_json(self, url, json, headers=None, timeout=None):
            calls["url"] = url
            calls["json"] = json
            calls["timeout"] = timeout
            return {"text": "result"}

    monkeypatch.setattr(llm, "_build_http_client", lambda timeout, integration: DummyClient())
    out = await llm._local_llm("prompt", 0.5, 8, timeout=1.2)
    assert out == "result"
    assert calls["url"].startswith("http://llm")
    assert calls.get("closed") is True
