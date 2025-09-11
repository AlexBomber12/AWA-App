import importlib
import os
import types

import pytest


@pytest.mark.asyncio
async def test_timeout_env_changes_timeout_used(monkeypatch):
    os.environ["TESTING"] = "1"
    os.environ["LLM_PROVIDER"] = "local"
    os.environ["LLM_TIMEOUT_SECS"] = "0.1"
    llm = importlib.reload(importlib.import_module("packages.awa_common.llm"))
    captured: dict[str, float | None] = {}

    class FakeClient:
        def __init__(self, *a, timeout=None, **kw):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **kw):
            class R:
                headers = {"content-type": "application/json"}

                def json(self):
                    return {"text": "ok"}

                @property
                def text(self):
                    return "ok"

                status_code = 200

                def raise_for_status(self):
                    pass

            return R()

    monkeypatch.setattr(
        llm,
        "httpx",
        types.SimpleNamespace(AsyncClient=FakeClient, TimeoutException=TimeoutError),
    )
    out = await llm.generate("hi")
    assert out == "ok"
    assert captured.get("timeout") == 0.1
