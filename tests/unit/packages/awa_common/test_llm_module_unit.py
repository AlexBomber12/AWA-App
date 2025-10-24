import types

import awa_common.llm as llm
import pytest


def test_timeout_seconds_handles_invalid(monkeypatch):
    monkeypatch.setenv("LLM_TIMEOUT_SECS", "bad")
    assert llm._timeout_seconds(3.5) == 3.5


@pytest.mark.asyncio
async def test_generate_stub_provider_returns_prefix():
    result = await llm._generate_with_provider(
        "stub", "hello world", temperature=0.1, max_tokens=32, timeout=1.0
    )
    assert result.startswith("[stub]")


@pytest.mark.asyncio
async def test_generate_local_provider_uses_httpx(monkeypatch):
    calls = {}

    class DummyResponse:
        headers = {"content-type": "application/json"}
        text = "fallback"

        def raise_for_status(self):
            return None

        def json(self):
            return {"completion": "success"}

    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers=None):
            calls["url"] = url
            calls["json"] = json
            calls["headers"] = headers
            return DummyResponse()

    monkeypatch.setattr(llm, "httpx", types.SimpleNamespace(AsyncClient=DummyClient))
    result = await llm._generate_with_provider(
        "local", "prompt text", temperature=0.5, max_tokens=64, timeout=2.0
    )
    assert result == "success"
    assert "prompt text" in calls["json"]["prompt"]


@pytest.mark.asyncio
async def test_generate_lan_provider_calls_remote(monkeypatch):
    recorded = {}

    class DummyResponse:
        headers = {"content-type": "application/json"}
        text = "remote"

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "lan response"}}]}

    class DummyClient:
        def __init__(self, *args, **kwargs):
            recorded["client_args"] = (args, kwargs)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers=None):
            recorded["url"] = url
            recorded["headers"] = headers
            recorded["json"] = json
            return DummyResponse()

    monkeypatch.setattr(llm, "httpx", types.SimpleNamespace(AsyncClient=DummyClient))
    result = await llm._generate_with_provider(
        "lan", "lan prompt", temperature=0.7, max_tokens=32, timeout=1.5
    )
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
        await llm._generate_with_provider(
            "openai", "prompt", temperature=0.2, max_tokens=16, timeout=1.0
        )
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
    monkeypatch.setenv("LLM_PROVIDER", "lan")
    result = await llm.generate("hello world", provider="lan", timeout=1.0)
    assert result == "[stub] done"
    assert attempts[0] == "lan"
    assert "stub" in attempts
