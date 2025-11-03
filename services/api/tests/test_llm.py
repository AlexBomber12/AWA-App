import os
import sys
import types

import pytest

from services.api.main import _check_llm


@pytest.mark.asyncio
async def test_check_llm_sets_fallback(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "lan")

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, url):
            raise RuntimeError("boom")

    monkeypatch.setattr("services.api.main.httpx.AsyncClient", lambda timeout=5: FakeClient())
    monkeypatch.setitem(
        sys.modules,
        "awa_common.llm",
        types.SimpleNamespace(
            LAN_BASE="http://x", LLM_PROVIDER="lan", LLM_PROVIDER_FALLBACK="stub"
        ),
    )
    await _check_llm()
    assert os.environ["LLM_PROVIDER"] == "stub"
