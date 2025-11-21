import importlib
from typing import Any, cast

from awa_common.http_client import AsyncHTTPClient

try:  # pragma: no cover - safeguards import order during bootstrapping
    from awa_common.settings import settings as _settings
except Exception:  # pragma: no cover - during bootstrap
    _settings = None


def _config():
    try:
        return getattr(_settings, "llm", None)
    except Exception:  # pragma: no cover - settings not initialised yet
        return None


def _default_timeout_setting() -> float:
    cfg = _config()
    if cfg is None:
        return 60.0
    return float(cfg.request_timeout_s)


_DEFAULT_LLM_TIMEOUT_S = _default_timeout_setting()


def _selected_provider() -> str:
    cfg = _config()
    if cfg is None:
        return "lan"
    return (cfg.provider or "lan").lower()


def _fallback_provider() -> str:
    cfg = _config()
    if cfg is None:
        return "stub"
    return (cfg.fallback_provider or "stub").lower()


def _timeout_seconds(default: float | None = None) -> float:
    if default is not None:
        return default
    cfg = _config()
    if cfg is None:
        return _DEFAULT_LLM_TIMEOUT_S
    return float(cfg.request_timeout_s)


def _build_http_client(timeout: float | None, integration: str) -> AsyncHTTPClient:
    resolved_timeout = _timeout_seconds(timeout)
    return AsyncHTTPClient(
        integration=integration,
        total_timeout_s=resolved_timeout,
        max_retries=1,
    )


async def _local_llm(prompt: str, temp: float, max_toks: int, timeout: float) -> str:
    cfg = _config()
    url = (cfg.remote_url if cfg else None) or (cfg.local_url if cfg else None) or "http://llm:8000/llm"
    async with _build_http_client(timeout, "llm_local") as cli:
        data = await cli.post_json(
            url,
            json={"prompt": prompt, "temperature": temp, "max_tokens": max_toks},
            timeout=timeout,
        )
    return cast(
        str,
        data.get("completion") or data.get("text") or data.get("content") or data,
    ).strip()


async def _openai_llm(prompt: str, temp: float, max_toks: int, timeout: float) -> str:
    openai: Any = importlib.import_module("openai")  # pragma: no cover - network
    cfg = _config()
    openai.api_key = (cfg.openai_api_key if cfg else None) or ""
    if cfg and cfg.openai_api_base:
        openai.api_base = cfg.openai_api_base
    model = (cfg.openai_model if cfg else None) or "gpt-4o-mini"
    rsp = await openai.ChatCompletion.acreate(  # pragma: no cover - network
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temp,
        max_tokens=max_toks,
        timeout=timeout,
    )
    return cast(str, rsp.choices[0].message.content).strip()  # pragma: no cover


async def _remote_generate(base: str, key: str | None, prompt: str, max_tokens: int, model: str, timeout: float) -> str:
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }
    cfg = _config()
    url = (cfg.remote_url if cfg else None) or f"{base}/v1/chat/completions"
    async with _build_http_client(timeout, "llm_remote") as cli:
        data = await cli.post_json(url, json=payload, headers=headers, timeout=timeout)
    return cast(
        str,
        data.get("choices", [{}])[0].get("message", {}).get("content")
        or data.get("text")
        or data.get("content")
        or data,
    ).strip()


async def _stub_llm(prompt: str, _temp: float, _max_toks: int) -> str:
    return "[stub] " + (prompt[:64] if prompt else "")


async def _generate_with_provider(
    provider: str,
    prompt: str,
    *,
    temperature: float,
    max_tokens: int,
    timeout: float | None = None,
) -> str:
    to = timeout or _timeout_seconds()
    if provider == "lan":
        cfg = _config()
        base = (cfg.lan_api_base_url if cfg else None) or "http://localhost:8000"
        key = (cfg.lan_api_key if cfg else None) or ""
        model = (cfg.openai_model if cfg else None) or "gpt-4o-mini"
        return await _remote_generate(base, key or None, prompt, max_tokens, model, timeout=to)
    if provider == "local":
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
    timeout: float | None = None,
) -> str:
    preferred = (provider or _selected_provider()).lower()
    fallback = _fallback_provider()
    providers = ["lan", "local", "openai", "stub"]
    if preferred in providers:
        providers.remove(preferred)
    providers.insert(0, preferred)
    if fallback in providers:
        providers.remove(fallback)
    providers.append(fallback)
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
        last_exc if last_exc else RuntimeError("LLM generation failed with no providers available")
    )  # pragma: no cover
