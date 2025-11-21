import importlib
import os

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.slow]


@pytest.fixture(autouse=True)
def _force_fast_llm_timeout(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_REQUEST_TIMEOUT_S", "0.05")


def _reload_llm():
    if "awa_common.llm" in list(importlib.sys.modules):
        importlib.reload(importlib.import_module("awa_common.llm"))
    return importlib.import_module("awa_common.llm")


@pytest.mark.slow
@pytest.mark.asyncio
async def test_timeout_on_lan_falls_back_to_stub(monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["LLM_PROVIDER"] = "lan"
    llm = _reload_llm()

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post_json(self, *_args, **_kwargs):
            raise TimeoutError("timeout")

    monkeypatch.setattr(llm, "_build_http_client", lambda timeout, integration: FakeClient())
    out = await llm.generate("hello")
    assert out.startswith("[stub]")


@pytest.mark.slow
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

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post_json(self, *_args, **_kwargs):
            return FakeResp().json()

    monkeypatch.setattr(llm, "_build_http_client", lambda timeout, integration: FakeClient())
    out = await llm.generate("ping")
    assert out == "LOCAL_OK"


@pytest.mark.slow
@pytest.mark.asyncio
async def test_openai_missing_module_falls_back(monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["LLM_PROVIDER"] = "openai"
    llm = _reload_llm()

    class FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post_json(self, *_args, **_kwargs):
            raise TimeoutError("offline")

    monkeypatch.setattr(llm, "_build_http_client", lambda timeout, integration: FailingClient())

    import sys

    if "openai" in sys.modules:
        del sys.modules["openai"]

    out = await llm.generate("xyz")
    assert out.startswith("[stub]")


@pytest.mark.slow
@pytest.mark.asyncio
async def test_unknown_provider_uses_stub(monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["LLM_PROVIDER"] = "totally-unknown"
    llm = _reload_llm()

    class FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post_json(self, *_args, **_kwargs):
            raise TimeoutError("offline")

    monkeypatch.setattr(llm, "_build_http_client", lambda timeout, integration: FailingClient())
    out = await llm.generate("zzz")
    assert out.startswith("[stub]")


@pytest.mark.slow
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

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post_json(self, *_args, **_kwargs):
            return FakeResp().json()

    monkeypatch.setattr(llm, "_build_http_client", lambda timeout, integration: FakeClient())
    assert (await llm.generate("1")) == "LOCAL_OK"

    os.environ["LLM_PROVIDER"] = "lan"

    class TClient(FakeClient):
        async def post_json(self, *_args, **_kwargs):
            raise TimeoutError("timeout")

    monkeypatch.setattr(llm, "_build_http_client", lambda timeout, integration: TClient())
    assert (await llm.generate("2")).startswith("[stub]")
