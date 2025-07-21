import importlib
import os
from typing import Any, cast

import httpx

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lan").lower()
LLM_PROVIDER_FALLBACK = os.getenv("LLM_PROVIDER_FALLBACK", "stub").lower()
LOCAL_URL = os.getenv("LLM_URL", "http://llm:8000/llm")
LAN_BASE = os.getenv("LLM_BASE_URL", "http://localhost:8000")
LAN_KEY = os.getenv("LLM_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


async def _local_llm(prompt: str, temp: float, max_toks: int) -> str:
    async with httpx.AsyncClient(timeout=60) as cli:
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


async def _remote_generate(
    base: str, key: str | None, prompt: str, max_tokens: int, model: str
) -> str:
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=60) as cli:
        resp = await cli.post(
            f"{base}/v1/chat/completions", json=payload, headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        return cast(str, data["choices"][0]["message"]["content"]).strip()


async def _stub_llm(prompt: str, temp: float, max_toks: int) -> str:
    return ""


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
        try:
            return await _remote_generate(
                LAN_BASE, LAN_KEY or None, prompt, max_tokens, OPENAI_MODEL
            )
        except Exception:
            if LLM_PROVIDER_FALLBACK != prov:
                return await generate(
                    prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    provider=LLM_PROVIDER_FALLBACK,
                )
            raise
    if prov == "local":
        return await _local_llm(prompt, temperature, max_tokens)
    if prov == "stub":
        return await _stub_llm(prompt, temperature, max_tokens)
    return await _local_llm(prompt, temperature, max_tokens)
