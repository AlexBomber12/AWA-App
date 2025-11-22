from __future__ import annotations

import types

import pytest

from awa_common import llm


class _StubLLMConfig:
    def __init__(self) -> None:
        self.provider = "local"
        self.secondary_provider = "cloud"
        self.base_url = "http://llm"
        self.provider_base_url = "http://provider"
        self.api_key = None
        self.request_timeout_s = 0.1
        self.local_model = "local-model"
        self.cloud_model = "gpt-5"
        self.allow_cloud_fallback = True
        self.email_cloud_threshold_chars = 0
        self.pricelist_cloud_threshold_rows = 0
        self.enable_email = True
        self.enable_pricelist = True
        self.min_confidence = 0.0


@pytest.mark.asyncio
async def test_classify_email_parses_response(monkeypatch):
    cfg = _StubLLMConfig()
    monkeypatch.setattr(llm, "_settings", types.SimpleNamespace(llm=cfg))
    client = llm.LLMClient()

    async def fake_post(body, provider, task):
        return {
            "result": {"intent": "price_list", "facts": {"currency": "USD"}, "confidence": 0.9},
            "provider": provider,
        }

    monkeypatch.setattr(client, "_post", fake_post)
    result = await client.classify_email(subject="s", body="body content", sender="buyer@example.com")
    assert result.intent == llm.EmailIntent.PRICE_LIST
    assert result.facts.currency == "USD"
    assert result.provider == "local"


@pytest.mark.asyncio
async def test_parse_price_list_fallbacks_to_cloud(monkeypatch):
    cfg = _StubLLMConfig()
    monkeypatch.setattr(llm, "_settings", types.SimpleNamespace(llm=cfg))
    client = llm.LLMClient()
    calls: list[str] = []

    async def fake_post(body, provider, task):
        calls.append(provider)
        if provider == "local":
            raise RuntimeError("unavailable")
        return {
            "result": {"detected_columns": {"sku": "SKU", "cost": "Price"}, "column_confidence": {"sku": 1.0}},
            "provider": provider,
        }

    monkeypatch.setattr(client, "_post", fake_post)
    result = await client.parse_price_list(preview={"headers": ["SKU"], "rows": []}, row_count=100)
    assert calls == ["local", "cloud"]
    assert result.detected_columns["sku"] == "SKU"
    assert result.provider == "cloud"


@pytest.mark.asyncio
async def test_generate_returns_completion(monkeypatch):
    cfg = _StubLLMConfig()
    cfg.enable_email = False
    cfg.enable_pricelist = False
    monkeypatch.setattr(llm, "_settings", types.SimpleNamespace(llm=cfg))
    client = llm.LLMClient()

    async def fake_post(body, provider, task):
        return {"result": {"completion": "done"}, "provider": provider}

    monkeypatch.setattr(client, "_post", fake_post)
    out = await client.generate("ping")
    assert out == "done"


@pytest.mark.asyncio
async def test_low_confidence_rejected(monkeypatch):
    cfg = _StubLLMConfig()
    cfg.min_confidence = 0.8
    monkeypatch.setattr(llm, "_settings", types.SimpleNamespace(llm=cfg))
    client = llm.LLMClient()

    async def fake_post(body, provider, task):
        return {"result": {"intent": "interested", "facts": {}, "confidence": 0.1}, "provider": provider}

    monkeypatch.setattr(client, "_post", fake_post)
    with pytest.raises(llm.LLMInvalidResponseError):
        await client.classify_email(subject="s", body="b", sender="x@y.com")
