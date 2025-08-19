import os, types, importlib, asyncio
import pytest

pytestmark = pytest.mark.unit


def _reload_llm():
    if "services.common.llm" in list(importlib.sys.modules):
        importlib.reload(importlib.import_module("services.common.llm"))
    return importlib.import_module("services.common.llm")


@pytest.mark.asyncio
async def test_timeout_on_lan_falls_back_to_stub(monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["LLM_PROVIDER"] = "lan"
    llm = _reload_llm()

    async def fake_post(*a, **kw):
        raise llm.httpx.TimeoutException("timeout") if hasattr(llm.httpx, "TimeoutException") else TimeoutError("timeout")

    class FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        post = fake_post

    monkeypatch.setattr(
        llm,
        "httpx",
        types.SimpleNamespace(AsyncClient=FakeClient, TimeoutException=TimeoutError),
    )
    out = await llm.generate("hello")
    assert out.startswith("[stub]")


@pytest.mark.asyncio
async def test_local_http_ok_no_fallback(monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["LLM_PROVIDER"] = "local"
    llm = _reload_llm()

    class FakeResp:
        status_code = 200
        headers = {"content-type": "application/json"}

        def json(self):
            return {"text": "LOCAL_OK"}

        @property
        def text(self):
            return "LOCAL_OK"

        def raise_for_status(self):
            pass

    async def fake_post(*a, **kw):
        return FakeResp()

    class FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        post = fake_post

    monkeypatch.setattr(
        llm,
        "httpx",
        types.SimpleNamespace(AsyncClient=FakeClient, TimeoutException=TimeoutError),
    )
    out = await llm.generate("ping")
    assert out == "LOCAL_OK"


@pytest.mark.asyncio
async def test_openai_missing_module_falls_back(monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["LLM_PROVIDER"] = "openai"
    llm = _reload_llm()

    import sys

    if "openai" in sys.modules:
        del sys.modules["openai"]

    out = await llm.generate("xyz")
    assert out.startswith("[stub]")


@pytest.mark.asyncio
async def test_unknown_provider_uses_stub(monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["LLM_PROVIDER"] = "totally-unknown"
    llm = _reload_llm()
    out = await llm.generate("zzz")
    assert out.startswith("[stub]")


@pytest.mark.asyncio
async def test_env_switch_effective_without_restart(monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["LLM_PROVIDER"] = "local"
    llm = _reload_llm()

    class FakeResp:
        status_code = 200
        headers = {"content-type": "application/json"}

        def json(self):
            return {"text": "LOCAL_OK"}

        @property
        def text(self):
            return "LOCAL_OK"

        def raise_for_status(self):
            pass

    async def fake_post(*a, **kw):
        return FakeResp()

    class FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        post = fake_post

    monkeypatch.setattr(
        llm,
        "httpx",
        types.SimpleNamespace(AsyncClient=FakeClient, TimeoutException=TimeoutError),
    )
    assert (await llm.generate("1")) == "LOCAL_OK"

    os.environ["LLM_PROVIDER"] = "lan"

    async def boom(*a, **kw):
        raise TimeoutError("timeout")

    class TClient(FakeClient):
        post = boom

    monkeypatch.setattr(
        llm,
        "httpx",
        types.SimpleNamespace(AsyncClient=TClient, TimeoutException=TimeoutError),
    )
    assert (await llm.generate("2")).startswith("[stub]")

