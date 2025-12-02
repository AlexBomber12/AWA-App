import pytest
from fastapi.testclient import TestClient

from services.llm_server import app as llm_app
from services.llm_server.errors import LLMProviderTimeoutError

client = TestClient(llm_app.app)


def test_llm_legacy_route(monkeypatch):
    async def fake_legacy(req: llm_app.LegacyRequest) -> dict[str, str]:
        return {"completion": "ok"}

    monkeypatch.setattr(llm_app, "_legacy_chat", fake_legacy)
    response = client.post("/llm", json={"prompt": "Hello", "max_tokens": 8})
    assert response.status_code == 200
    payload = response.json()
    assert payload["task"] == "chat_completion"
    assert payload["result"] == "ok"


@pytest.mark.asyncio
async def test_run_task_classify_email(monkeypatch):
    async def fake_provider(req: llm_app.LLMRequest, provider: str) -> dict:
        return {"intent": "question", "facts": {"contacts": []}, "confidence": 0.9}

    monkeypatch.setattr(llm_app, "_call_provider", fake_provider)
    req = llm_app.LLMRequest(task="classify_email", input={"body": "hi"}, provider="local")
    result = await llm_app._run_task(req, "local")
    assert result["intent"] == "question"


@pytest.mark.asyncio
async def test_run_task_parse_price_list(monkeypatch):
    async def fake_provider(req: llm_app.LLMRequest, provider: str) -> dict:
        return {
            "detected_columns": {"vendor_sku": "SKU"},
            "column_confidence": {"vendor_sku": 0.9},
            "needs_review": False,
        }

    monkeypatch.setattr(llm_app, "_call_provider", fake_provider)
    req = llm_app.LLMRequest(task="parse_price_list", input={"headers": ["sku"], "rows": []}, provider="cloud")
    result = await llm_app._run_task(req, "cloud")
    assert result["detected_columns"]["vendor_sku"] == "SKU"


@pytest.mark.asyncio
async def test_run_task_chat_completion(monkeypatch):
    async def fake_provider(req: llm_app.LLMRequest, provider: str) -> dict:
        return {"completion": "hello world"}

    monkeypatch.setattr(llm_app, "_call_provider", fake_provider)
    req = llm_app.LLMRequest(task="chat_completion", input={"prompt": "hello"}, provider="local")
    result = await llm_app._run_task(req, "local")
    assert result == "hello world"


def test_llm_timeout_error_response(monkeypatch):
    async def failing_provider(req: llm_app.LLMRequest, provider: str):
        raise LLMProviderTimeoutError()

    monkeypatch.setattr(llm_app, "_call_provider", failing_provider)
    response = client.post("/llm", json={"task": "chat_completion", "input": {"prompt": "hi"}, "provider": "cloud"})
    assert response.status_code == 504
    payload = response.json()
    assert payload["error"]["type"] == "provider_timeout"
    assert "message" in payload["error"]
