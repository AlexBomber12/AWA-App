import os

import pytest

from services.api import main


class DummyClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url: str) -> None:  # pragma: no cover - raise error
        raise RuntimeError("fail")


@pytest.mark.asyncio
async def test_check_llm(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "lan")
    monkeypatch.setenv("LLM_PROVIDER_FALLBACK", "stub")
    monkeypatch.setattr(main.httpx, "AsyncClient", lambda timeout: DummyClient())
    await main._check_llm()
    assert os.environ["LLM_PROVIDER"] == "stub"
