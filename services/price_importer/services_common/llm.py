from __future__ import annotations

from typing import cast

from awa_common.http_client import AsyncHTTPClient
from awa_common.llm import (
    EmailLLMResult,
    LLMClient,
    PriceListLLMResult,
    classify_email,
    generate,
    parse_price_list,
)
from awa_common.settings import settings

_LLM_CFG = getattr(settings, "llm", None)
LLM_TIMEOUT_S = float(getattr(_LLM_CFG, "request_timeout_s", getattr(settings, "LLM_REQUEST_TIMEOUT_S", 60.0)))


def _llm_client(integration: str) -> AsyncHTTPClient:
    return AsyncHTTPClient(
        integration=integration,
        total_timeout_s=LLM_TIMEOUT_S,
        max_retries=1,
    )


async def _local_llm(prompt: str, temp: float, max_toks: int) -> str:
    async with _llm_client("llm_local") as cli:
        data = await cli.post_json(
            getattr(_LLM_CFG, "base_url", "http://localhost:8000/llm"),
            json={"prompt": prompt, "temperature": temp, "max_tokens": max_toks},
            timeout=LLM_TIMEOUT_S,
        )
    return cast(str, data.get("completion") or data.get("text") or data)


async def _remote_generate(base: str, key: str | None, prompt: str, max_tokens: int, model: str) -> str:
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    async with _llm_client("llm_remote") as cli:
        data = await cli.post_json(
            f"{base}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=LLM_TIMEOUT_S,
        )
    return cast(str, data.get("choices", [{}])[0].get("message", {}).get("content") or data)


__all__ = [
    "LLMClient",
    "generate",
    "classify_email",
    "parse_price_list",
    "EmailLLMResult",
    "PriceListLLMResult",
    "_llm_client",
    "_local_llm",
    "_remote_generate",
    "LLM_TIMEOUT_S",
]
