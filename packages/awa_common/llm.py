from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from enum import Enum
from typing import Any, Literal

import structlog
from pydantic import BaseModel, Field, ValidationError

from awa_common.http_client import AsyncHTTPClient
from awa_common.metrics import (
    record_llm_error,
    record_llm_fallback,
    record_llm_request,
)

try:  # pragma: no cover - safeguards import order during bootstrapping
    from awa_common.settings import settings as _settings
except Exception:  # pragma: no cover - settings not initialised yet
    _settings = None

ProviderType = Literal["local", "cloud"]
_SUPPORTED_PROVIDERS: set[str] = {"local", "cloud"}

logger = structlog.get_logger(__name__).bind(component="llm_client")


class EmailIntent(str, Enum):
    INTERESTED = "interested"
    PRICE_LIST = "price_list"
    COMPLAINT = "complaint"
    NEGOTIATION = "negotiation"
    QUESTION = "question"
    OOO = "ooo"
    NOT_INTERESTED = "not_interested"
    AUTO_REPLY = "auto_reply"
    BOUNCE = "bounce"
    WRONG_CONTACT = "wrong_contact"


class Contact(BaseModel):
    name: str | None = None
    role: str | None = None
    email: str | None = None
    phone: str | None = None


class EmailFacts(BaseModel):
    currency: str | None = None
    incoterms: str | None = None
    moq: int | None = None
    lead_time_days: int | None = None
    price_link: str | None = None
    contacts: list[Contact] = Field(default_factory=list)
    additional_hints: dict[str, Any] = Field(default_factory=dict)


class EmailLLMResult(BaseModel):
    intent: EmailIntent
    facts: EmailFacts = Field(default_factory=EmailFacts)
    confidence: float | None = None
    provider: str | None = None


class PriceListMetadata(BaseModel):
    vendor_name: str | None = None
    country: str | None = None
    detected_currency: str | None = None
    date_range: str | None = None
    notes: dict[str, Any] = Field(default_factory=dict)


class PriceListLLMResult(BaseModel):
    detected_columns: dict[str, str] = Field(default_factory=dict)
    global_metadata: PriceListMetadata | None = None
    column_confidence: dict[str, float] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    needs_review: bool = False
    provider: str | None = None


class LLMError(Exception):
    """Base exception for LLM failures."""


class LLMInvalidResponseError(LLMError):
    """Raised when the LLM returns malformed or un-parseable content."""


class LLMConfigurationError(LLMError):
    """Raised when the LLM client is misconfigured."""


def _config():
    try:
        return getattr(_settings, "llm", None)
    except Exception:  # pragma: no cover - settings not initialised yet
        return None


class LLMClient:
    """Typed helper wrapper around the LLM microservice."""

    def __init__(self, *, http_client_factory: Callable[[str], AsyncHTTPClient] | None = None):
        cfg = _config()
        if cfg is None:
            raise LLMConfigurationError("LLM settings not initialised")
        self._cfg = cfg
        self.base_url = (cfg.base_url or "http://localhost:8000").rstrip("/")
        self.api_key = cfg.api_key or None
        self.timeout = float(cfg.request_timeout_s)
        self.default_provider = self._normalise_provider(cfg.provider)
        secondary = getattr(cfg, "secondary_provider", None) or None
        self.secondary_provider = self._normalise_provider(secondary) if secondary else None
        self.local_model = getattr(cfg, "local_model", None) or "gpt-4o-mini"
        self.cloud_model = getattr(cfg, "cloud_model", None) or "gpt-5"
        self.allow_cloud_fallback = bool(getattr(cfg, "allow_cloud_fallback", False))
        self.email_cloud_threshold_chars = int(getattr(cfg, "email_cloud_threshold_chars", 0) or 0)
        self.pricelist_cloud_threshold_rows = int(getattr(cfg, "pricelist_cloud_threshold_rows", 0) or 0)
        self.enable_email = bool(getattr(cfg, "enable_email", False))
        self.enable_pricelist = bool(getattr(cfg, "enable_pricelist", False))
        self.min_confidence = float(getattr(cfg, "min_confidence", 0.0) or 0.0)
        self._http_client_factory = http_client_factory or self._build_http_client

    def _normalise_provider(self, provider: str | None) -> ProviderType:
        prov = (provider or "local").lower()
        if prov not in _SUPPORTED_PROVIDERS:
            raise LLMConfigurationError(f"Unsupported LLM provider: {prov}")
        return prov  # type: ignore[return-value]

    def _build_http_client(self, integration: str) -> AsyncHTTPClient:
        return AsyncHTTPClient(
            integration=integration,
            total_timeout_s=self.timeout,
            max_retries=1,
        )

    def _provider_for_task(
        self,
        task: str,
        *,
        provider_hint: str | None = None,
        size_hint: int | None = None,
        row_count: int | None = None,
        complexity_tags: Sequence[str] | None = None,
    ) -> ProviderType:
        if provider_hint:
            return self._normalise_provider(provider_hint)
        if self.secondary_provider == "cloud":
            if (
                task == "classify_email"
                and self.email_cloud_threshold_chars
                and (size_hint or 0) > self.email_cloud_threshold_chars
            ):
                logger.info(
                    "llm.provider.selected",
                    task=task,
                    provider="cloud",
                    reason="email_length_threshold",
                    size=size_hint,
                    threshold=self.email_cloud_threshold_chars,
                )
                return "cloud"
            if task == "parse_price_list":
                if (
                    row_count
                    and self.pricelist_cloud_threshold_rows
                    and row_count > self.pricelist_cloud_threshold_rows
                ):
                    logger.info(
                        "llm.provider.selected",
                        task=task,
                        provider="cloud",
                        reason="row_threshold",
                        row_count=row_count,
                        threshold=self.pricelist_cloud_threshold_rows,
                    )
                    return "cloud"
                if complexity_tags:
                    logger.info(
                        "llm.provider.selected",
                        task=task,
                        provider="cloud",
                        reason="complexity_tags",
                        tags=list(complexity_tags),
                    )
                    return "cloud"
        return self.default_provider

    def _model_for(self, provider: ProviderType) -> str:
        return self.cloud_model if provider == "cloud" else self.local_model

    def _headers(self) -> Mapping[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    async def _post(
        self, body: dict[str, Any], *, provider: ProviderType, task: str
    ) -> dict[str, Any]:  # pragma: no cover - network boundary
        start = time.perf_counter()
        outcome = "error"
        url = f"{self.base_url}/llm"
        try:
            async with self._http_client_factory("llm_service") as cli:
                data = await cli.post_json(url, json=body, headers=self._headers(), timeout=self.timeout)
            outcome = "success"
            return data if isinstance(data, dict) else {"result": data}
        except Exception as exc:
            record_llm_error(task, provider, exc.__class__.__name__)
            logger.warning(
                "llm.request.failed",
                task=task,
                provider=provider,
                error=str(exc),
                error_type=exc.__class__.__name__,
            )
            raise
        finally:
            record_llm_request(task, provider, outcome, time.perf_counter() - start)

    def _extract_result(self, task: str, data: Mapping[str, Any]) -> tuple[Mapping[str, Any], ProviderType]:
        provider = (
            (data.get("provider") or self.default_provider) if isinstance(data, Mapping) else self.default_provider
        )
        prov = self._normalise_provider(str(provider))
        if isinstance(data, Mapping):
            if "result" in data:
                payload = data["result"]
                if task == "chat_completion" and not isinstance(payload, Mapping):
                    return {"completion": payload}, prov
                if isinstance(payload, Mapping):
                    return payload, prov
            if task == "chat_completion" and isinstance(data.get("completion"), str):
                return {"completion": data["completion"]}, prov
        raise LLMInvalidResponseError(f"LLM response missing expected JSON payload for task={task}")

    def _should_fallback(self, provider: ProviderType) -> bool:
        return self.allow_cloud_fallback and provider != "cloud" and self.secondary_provider == "cloud"

    async def _execute(
        self,
        *,
        task: str,
        provider: ProviderType,
        body: dict[str, Any],
        model_cls: type[BaseModel] | None = None,
    ) -> tuple[Any, ProviderType]:
        try:
            response = await self._post(body, provider=provider, task=task)
        except Exception as exc:
            if self._should_fallback(provider):
                return await self._fallback(
                    task=task, from_provider=provider, body=body, model_cls=model_cls, error=exc
                )
            raise

        try:
            parsed, prov_used = self._extract_result(task, response)
            if model_cls is None:
                return parsed, prov_used
            return model_cls.model_validate(parsed), prov_used
        except ValidationError as exc:
            record_llm_error(task, provider, "validation_error")
            if self._should_fallback(provider):
                return await self._fallback(
                    task=task,
                    from_provider=provider,
                    body=body,
                    model_cls=model_cls,
                    error=exc,
                )
            raise LLMInvalidResponseError(f"LLM response failed validation for task={task}") from exc
        except LLMInvalidResponseError:
            record_llm_error(task, provider, "invalid_response")
            if self._should_fallback(provider):
                return await self._fallback(
                    task=task,
                    from_provider=provider,
                    body=body,
                    model_cls=model_cls,
                    error=None,
                )
            raise

    async def _fallback(  # pragma: no cover - exercised via higher-level tests
        self,
        *,
        task: str,
        from_provider: ProviderType,
        body: dict[str, Any],
        model_cls: type[BaseModel] | None,
        error: Exception | None,
    ) -> tuple[Any, ProviderType]:
        record_llm_fallback(task, from_provider, "cloud", error.__class__.__name__ if error else "retry")
        logger.info(
            "llm.provider.fallback",
            task=task,
            from_provider=from_provider,
            to_provider="cloud",
            error=str(error) if error else None,
        )
        fallback_body = dict(body)
        fallback_body["provider"] = "cloud"
        fallback_body["model"] = self._model_for("cloud")
        response = await self._post(fallback_body, provider="cloud", task=task)
        parsed, prov_used = self._extract_result(task, response)
        if model_cls is None:
            return parsed, prov_used
        try:
            return model_cls.model_validate(parsed), prov_used
        except ValidationError as exc:
            record_llm_error(task, "cloud", "validation_error")
            raise LLMInvalidResponseError(f"LLM fallback response failed validation for task={task}") from exc

    def _build_payload(
        self,
        task: str,
        provider: ProviderType,
        input_payload: Mapping[str, Any],
        *,
        temperature: float = 0.0,
        max_tokens: int = 800,
        priority: str | None = None,
        schema: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "task": task,
            "provider": provider,
            "model": self._model_for(provider),
            "input": dict(input_payload),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "schema": dict(schema) if schema else None,
            "priority": priority,
        }
        return payload

    async def classify_email(
        self,
        *,
        subject: str,
        body: str,
        sender: str,
        to: Sequence[str] | None = None,
        cc: Sequence[str] | None = None,
        has_price_list_attachment: bool = False,
        language: str | None = None,
        provider_hint: str | None = None,
        priority: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> EmailLLMResult:
        if not self.enable_email:
            raise LLMConfigurationError("Email LLM integration is disabled via configuration")
        to_list = list(to or [])
        cc_list = list(cc or [])
        payload = {
            "subject": subject or "",
            "body": body or "",
            "sender": sender or "",
            "to": to_list,
            "cc": cc_list,
            "has_price_list_attachment": bool(has_price_list_attachment),
            "language": language,
            "metadata": dict(metadata or {}),
        }
        provider = self._provider_for_task(
            "classify_email",
            provider_hint=provider_hint,
            size_hint=len(body or ""),
        )
        body_payload = self._build_payload(
            "classify_email",
            provider,
            payload,
            temperature=0.0,
            max_tokens=800,
            priority=priority,
            schema=EmailLLMResult.model_json_schema(),
        )
        result, prov_used = await self._execute(
            task="classify_email",
            provider=provider,
            body=body_payload,
            model_cls=EmailLLMResult,
        )
        if isinstance(result, EmailLLMResult):
            result.provider = prov_used
        if result.confidence is not None and result.confidence < self.min_confidence:
            raise LLMInvalidResponseError("Email classification confidence below threshold")
        return result

    async def parse_price_list(
        self,
        *,
        preview: Mapping[str, Any],
        provider_hint: str | None = None,
        row_count: int | None = None,
        complexity_tags: Sequence[str] | None = None,
        priority: str | None = None,
    ) -> PriceListLLMResult:
        if not self.enable_pricelist:
            raise LLMConfigurationError("Price list LLM integration is disabled via configuration")
        provider = self._provider_for_task(
            "parse_price_list",
            provider_hint=provider_hint,
            row_count=row_count,
            complexity_tags=complexity_tags,
        )
        body_payload = self._build_payload(
            "parse_price_list",
            provider,
            preview,
            temperature=0.0,
            max_tokens=1200,
            priority=priority,
            schema=PriceListLLMResult.model_json_schema(),
        )
        result, prov_used = await self._execute(
            task="parse_price_list",
            provider=provider,
            body=body_payload,
            model_cls=PriceListLLMResult,
        )
        if isinstance(result, PriceListLLMResult):
            result.provider = prov_used  # type: ignore[attr-defined]
            if result.needs_review or any(
                (c is not None and c < self.min_confidence) for c in result.column_confidence.values()
            ):
                raise LLMInvalidResponseError("Price list parsing flagged for manual review")
        return result

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 256,
        provider: str | None = None,
    ) -> str:
        provider_for_task = self._provider_for_task("chat_completion", provider_hint=provider)
        payload = self._build_payload(
            "chat_completion",
            provider_for_task,
            {"prompt": prompt},
            temperature=temperature,
            max_tokens=max_tokens,
        )
        data, _prov_used = await self._execute(
            task="chat_completion",
            provider=provider_for_task,
            body=payload,
            model_cls=None,
        )
        if isinstance(data, Mapping):
            completion = (
                data.get("completion")
                or data.get("text")
                or data.get("content")
                or data.get("choices", [{}])[0].get("message", {}).get("content")
            )
        else:
            completion = data
        if completion is None:
            raise LLMInvalidResponseError("LLM completion missing content")
        return str(completion).strip()


async def classify_email(**kwargs: Any) -> EmailLLMResult:
    client = LLMClient()
    return await client.classify_email(**kwargs)


async def parse_price_list(**kwargs: Any) -> PriceListLLMResult:
    client = LLMClient()
    return await client.parse_price_list(**kwargs)


async def generate(
    prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 256,
    provider: str | None = None,
) -> str:
    client = LLMClient()
    return await client.generate(prompt, temperature=temperature, max_tokens=max_tokens, provider=provider)
