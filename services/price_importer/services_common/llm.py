from __future__ import annotations

import importlib
from typing import Any, cast

import httpx

from awa_common.settings import settings

_LLM_CFG = getattr(settings, "llm", None)
LLM_PROVIDER = (_LLM_CFG.provider if _LLM_CFG else "lan").lower()
LOCAL_URL = (_LLM_CFG.local_url if _LLM_CFG else None) or "http://llm:8000/llm"
LAN_BASE = (_LLM_CFG.lan_api_base_url if _LLM_CFG else None) or "http://localhost:8000"
LAN_KEY = (_LLM_CFG.lan_api_key if _LLM_CFG else None) or ""
OPENAI_MODEL = (_LLM_CFG.openai_model if _LLM_CFG else None) or "gpt-4o-mini"
OPENAI_API_KEY = (_LLM_CFG.openai_api_key if _LLM_CFG else None) or ""
LLM_TIMEOUT_S = float(getattr(_LLM_CFG, "request_timeout_s", getattr(settings, "LLM_REQUEST_TIMEOUT_S", 60.0)))


async def _local_llm(prompt: str, temp: float, max_toks: int) -> str:
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT_S) as cli:
        r = await cli.post(
            LOCAL_URL,
            json={"prompt": prompt, "temperature": temp, "max_tokens": max_toks},
        )
        r.raise_for_status()
        return cast(str, r.json()["completion"])


async def _openai_llm(prompt: str, temp: float, max_toks: int) -> str:
    openai: Any = importlib.import_module("openai")
    openai.api_key = OPENAI_API_KEY
    rsp = await openai.ChatCompletion.acreate(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temp,
        max_tokens=max_toks,
    )
    return cast(str, rsp.choices[0].message.content).strip()


async def _remote_generate(base: str, key: str | None, prompt: str, max_tokens: int, model: str) -> str:
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT_S) as cli:
        resp = await cli.post(f"{base}/v1/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return cast(str, data["choices"][0]["message"]["content"]).strip()


async def generate(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 256,
    provider: str | None = None,
) -> str:
    prov = (provider or LLM_PROVIDER).lower()
    if prov == "openai":
        return await _openai_llm(prompt, temperature, max_tokens)
    if prov == "lan":
        return await _remote_generate(LAN_BASE, LAN_KEY or None, prompt, max_tokens, OPENAI_MODEL)
    return await _local_llm(prompt, temperature, max_tokens)
