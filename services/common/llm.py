import importlib
import os
from typing import Any, Optional, cast

try:
    import httpx
except Exception:  # pragma: no cover - httpx is available in production
    httpx = None
LOCAL_URL = os.getenv("LLM_URL", "http://llm:8000/llm")
LAN_BASE = os.getenv("LLM_BASE_URL", "http://localhost:8000")
LAN_KEY = os.getenv("LLM_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


_LLM_PROVIDER_ENV = "LLM_PROVIDER"
LLM_PROVIDER = os.getenv(_LLM_PROVIDER_ENV, "lan").strip().lower()
LLM_PROVIDER_FALLBACK = os.getenv("LLM_PROVIDER_FALLBACK", "stub").strip().lower()
_LLM_TIMEOUT_ENV = "LLM_TIMEOUT_SECS"
_REMOTE_URL_ENV = "LLM_REMOTE_URL"


def _selected_provider() -> str:
    return (os.getenv("LLM_PROVIDER") or "lan").strip().lower()


def _timeout_seconds(default: float = 60.0) -> float:
    try:
        return float(os.getenv(_LLM_TIMEOUT_ENV, str(default)))
    except Exception:  # pragma: no cover - env parsing failure
        return default


async def _local_llm(prompt: str, temp: float, max_toks: int, timeout: float) -> str:
    url = os.getenv(_REMOTE_URL_ENV) or LOCAL_URL
    async with httpx.AsyncClient(timeout=timeout) as cli:
        r = await cli.post(
            url, json={"prompt": prompt, "temperature": temp, "max_tokens": max_toks}
        )
        r.raise_for_status()
        data = (
            r.json() if "application/json" in r.headers.get("content-type", "") else {}
        )
        return cast(
            str,
            data.get("completion") or data.get("text") or data.get("content") or r.text,
        ).strip()


async def _openai_llm(prompt: str, temp: float, max_toks: int, timeout: float) -> str:
    openai: Any = importlib.import_module("openai")  # pragma: no cover - network
    openai.api_key = OPENAI_API_KEY
    rsp = await openai.ChatCompletion.acreate(  # pragma: no cover - network
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temp,
        max_tokens=max_toks,
        timeout=timeout,
    )
    return cast(str, rsp.choices[0].message.content).strip()  # pragma: no cover


async def _remote_generate(
    base: str, key: str | None, prompt: str, max_tokens: int, model: str, timeout: float
) -> str:
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    url = os.getenv(_REMOTE_URL_ENV) or f"{base}/v1/chat/completions"
    async with httpx.AsyncClient(timeout=timeout) as cli:
        resp = await cli.post(url, json=payload, headers=headers)
        resp.raise_for_status()  # pragma: no cover - network error path
        try:
            data = resp.json()
        except Exception:  # pragma: no cover - non-json response
            data = {}
        text = getattr(resp, "text", "")
        return cast(
            str,
            data.get("choices", [{}])[0].get("message", {}).get("content")
            or data.get("text")
            or data.get("content")
            or text,
        ).strip()


async def _stub_llm(prompt: str, temp: float, max_toks: int) -> str:
    return "[stub] " + (prompt[:64] if prompt else "")


async def _generate_with_provider(
    provider: str,
    prompt: str,
    *,
    temperature: float,
    max_tokens: int,
    timeout: Optional[float] = None,
) -> str:
    to = timeout or _timeout_seconds()
    if provider == "lan":
        if httpx is None:  # pragma: no cover - dependency guard
            raise RuntimeError("httpx not available for lan provider")
        return await _remote_generate(
            LAN_BASE, LAN_KEY or None, prompt, max_tokens, OPENAI_MODEL, timeout=to
        )
    if provider == "local":
        if httpx is None:  # pragma: no cover - dependency guard
            raise RuntimeError("httpx not available for local provider")
        return await _local_llm(prompt, temperature, max_tokens, timeout=to)
    if provider == "openai":
        try:
            return await _openai_llm(prompt, temperature, max_tokens, timeout=to)
        except Exception as e:  # pragma: no cover - exercised in tests
            raise RuntimeError("openai provider call failed") from e
    if provider == "stub":
        return await _stub_llm(prompt, temperature, max_tokens)
    raise ValueError(f"Unknown provider: {provider}")  # pragma: no cover


async def generate(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 256,
    provider: str | None = None,
    *,
    timeout: Optional[float] = None,
) -> str:
    env_prov = _selected_provider()
    prov = (provider or env_prov).lower()
    providers = ["lan", "local", "openai", "stub"]
    if prov in providers:
        providers.remove(prov)
        providers.insert(0, prov)
    last_exc: Exception | None = None
    for p in providers:
        try:
            return await _generate_with_provider(
                p,
                prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
        except Exception as e:
            last_exc = e
    raise (
        last_exc
        if last_exc
        else RuntimeError("LLM generation failed with no providers available")
    )  # pragma: no cover
