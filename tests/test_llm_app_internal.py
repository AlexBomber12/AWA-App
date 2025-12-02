import pytest
from fastapi.testclient import TestClient

from services.llm_server import app as llm_app
from services.llm_server.errors import (
    LLMBinaryOSFailure,
    LLMProviderServerError,
    LLMServiceError,
)


@pytest.mark.anyio
async def test_legacy_chat_truncated(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_run(*args, **kwargs):
        return "hello\n", True

    monkeypatch.setattr(llm_app, "run_llm_binary", fake_run)
    result = await llm_app._legacy_chat(llm_app.LegacyRequest(prompt="hi"))
    assert result["completion"].endswith("[truncated]")


def test_extract_content_with_choices() -> None:
    payload = {"choices": [{"message": {"content": '{"ok":true}'}}]}
    assert llm_app._extract_content(payload) == '{"ok":true}'
    assert llm_app._extract_content({"completion": "done"}) == "done"
    assert llm_app._extract_content({"text": "alt"}) == "alt"


def test_provider_client_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_app, "_PROVIDER_CLIENTS", {})
    with pytest.raises(LLMServiceError):
        llm_app._provider_client("local")


def test_build_payload_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    req = llm_app.LLMRequest(task="chat_completion", input={"prompt": "hi"}, priority="p1", provider="cloud")
    payload = llm_app._build_payload(req, "cloud")
    assert payload["priority"] == "p1"
    assert payload["model"] == llm_app.CLOUD_MODEL


@pytest.mark.anyio
async def test_run_task_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_call(_req: llm_app.LLMRequest, _provider: str):
        return {"intent": "missing_fields"}

    monkeypatch.setattr(llm_app, "_call_provider", fake_call)
    req = llm_app.LLMRequest(task="classify_email", input={"body": "hi"}, provider="local")
    with pytest.raises(LLMServiceError) as exc:
        await llm_app._run_task(req, "local")
    assert exc.value.error_type == "validation_error"


@pytest.mark.anyio
async def test_run_task_invalid_response(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_call(_req: llm_app.LLMRequest, _provider: str):
        return 123  # not JSON or mapping

    monkeypatch.setattr(llm_app, "_call_provider", fake_call)
    req = llm_app.LLMRequest(task="parse_price_list", input={"headers": [], "rows": []}, provider="cloud")
    with pytest.raises(LLMServiceError) as exc:
        await llm_app._run_task(req, "cloud")
    assert exc.value.error_type == "invalid_response"


@pytest.mark.anyio
async def test_run_task_provider_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_call(_req: llm_app.LLMRequest, _provider: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(llm_app, "_call_provider", failing_call)
    req = llm_app.LLMRequest(task="chat_completion", input={"prompt": "x"}, provider="local")
    with pytest.raises(LLMServiceError) as exc:
        await llm_app._run_task(req, "local")
    assert exc.value.error_type == "provider_error"


def test_health_unconfigured_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_app, "_PROVIDER_CLIENTS", {})
    monkeypatch.setattr(llm_app, "LOCAL_BASE", "")
    monkeypatch.setattr(llm_app, "BIN", "/nonexistent/bin")
    client = TestClient(llm_app.app)
    resp = client.get("/health")
    assert resp.status_code == 503
    body = resp.json()
    assert body["status"] == "error"
    assert any("Provider client not configured" in err or "binary" in err for err in body["errors"])


def test_error_as_dict_includes_details() -> None:
    err = LLMProviderServerError(provider="cloud", status=503)
    data = err.as_dict()
    assert data["provider"] == "cloud"
    assert data["details"]["provider_status"] == 503

    os_err = LLMBinaryOSFailure("fail")
    os_data = os_err.as_dict()
    assert os_data["type"] == "bin_os_error"


def test_completion_from_result_variants() -> None:
    assert llm_app._completion_from_result({"completion": "done"}) == "done"
    assert llm_app._completion_from_result({"text": "alt"}) == "alt"
    assert llm_app._completion_from_result({"content": "msg"}) == "msg"
    assert llm_app._completion_from_result({"other": "x"}) == '{"other": "x"}'


@pytest.mark.anyio
async def test_handle_legacy_binary_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_run(*args, **kwargs):
        raise LLMBinaryOSFailure("no bin")

    monkeypatch.setattr(llm_app, "run_llm_binary", failing_run)
    with pytest.raises(LLMBinaryOSFailure):
        await llm_app._handle_legacy(llm_app.LegacyRequest(prompt="hi"))


def test_ready_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(llm_app.app)
    resp = client.get("/ready")
    assert resp.status_code in {200, 503}


def test_health_with_invalid_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_app, "REQUEST_TIMEOUT", 0)
    monkeypatch.setattr(llm_app, "REQUEST_RETRIES", 0)
    monkeypatch.setattr(llm_app, "MAX_OUTPUT_BYTES", 0)
    monkeypatch.setattr(llm_app, "_PROVIDER_CLIENTS", {})
    resp = TestClient(llm_app.app).get("/health")
    assert resp.status_code == 503
    assert "LLM_REQUEST_TIMEOUT_SEC must be positive" in resp.json()["errors"][0]
