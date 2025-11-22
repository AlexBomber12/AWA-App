import subprocess

import pytest
from fastapi.testclient import TestClient

from services.llm_server import app as llm_app

client = TestClient(llm_app.app)


def test_llm(monkeypatch):
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: b"ok")
    r = client.post("/llm", json={"prompt": "Hello", "max_tokens": 8})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_run_task_classify_email(monkeypatch):
    async def fake_local(req: llm_app.LLMRequest) -> dict:
        return {"intent": "question", "facts": {"contacts": []}, "confidence": 0.9}

    monkeypatch.setattr(llm_app, "_call_local", fake_local)
    req = llm_app.LLMRequest(task="classify_email", input={"body": "hi"}, provider="local")
    result = await llm_app._run_task(req, "local")
    assert result["intent"] == "question"


@pytest.mark.asyncio
async def test_run_task_parse_price_list(monkeypatch):
    async def fake_cloud(req: llm_app.LLMRequest) -> dict:
        return {
            "detected_columns": {"vendor_sku": "SKU"},
            "column_confidence": {"vendor_sku": 0.9},
            "needs_review": False,
        }

    monkeypatch.setattr(llm_app, "_call_cloud", fake_cloud)
    req = llm_app.LLMRequest(task="parse_price_list", input={"headers": ["sku"], "rows": []}, provider="cloud")
    result = await llm_app._run_task(req, "cloud")
    assert result["detected_columns"]["vendor_sku"] == "SKU"


@pytest.mark.asyncio
async def test_run_task_chat_completion(monkeypatch):
    async def fake_local(req: llm_app.LLMRequest) -> dict:
        return {"completion": "hello world"}

    monkeypatch.setattr(llm_app, "_call_local", fake_local)
    req = llm_app.LLMRequest(task="chat_completion", input={"prompt": "hello"}, provider="local")
    result = await llm_app._run_task(req, "local")
    assert result == "hello world"
