from __future__ import annotations

from typing import Any


class LLMServiceError(Exception):
    """Base exception for LLM server failures that should map to HTTP responses."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        error_type: str = "llm_error",
        provider: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.provider = provider
        self.details = details or {}

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.error_type, "message": self.message}
        if self.provider:
            payload["provider"] = self.provider
        if self.details:
            payload["details"] = self.details
        return payload


class LLMProviderError(LLMServiceError):
    """Base exception for upstream provider issues."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        error_type: str = "provider_error",
        provider: str | None = None,
        provider_status: int | None = None,
    ) -> None:
        details = {"provider_status": provider_status} if provider_status is not None else {}
        super().__init__(
            message,
            status_code=status_code,
            error_type=error_type,
            provider=provider,
            details=details,
        )
        self.provider_status = provider_status


class LLMProviderTimeoutError(LLMProviderError):
    def __init__(self, message: str = "LLM provider timed out", *, provider: str | None = None) -> None:
        super().__init__(message, status_code=504, error_type="provider_timeout", provider=provider)


class LLMProviderClientError(LLMProviderError):
    def __init__(
        self,
        message: str = "LLM provider rejected the request",
        *,
        provider: str | None = None,
        status: int | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=502,
            error_type="provider_client_error",
            provider=provider,
            provider_status=status,
        )


class LLMProviderServerError(LLMProviderError):
    def __init__(
        self, message: str = "LLM provider failed", *, provider: str | None = None, status: int | None = None
    ) -> None:
        super().__init__(
            message,
            status_code=502,
            error_type="provider_server_error",
            provider=provider,
            provider_status=status,
        )


class LLMProviderTransportError(LLMProviderError):
    def __init__(self, message: str = "LLM provider transport failed", *, provider: str | None = None) -> None:
        super().__init__(message, status_code=502, error_type="provider_transport_error", provider=provider)


class LLMBinaryError(LLMServiceError):
    """Base exception for local binary execution failures."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        error_type: str = "bin_error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, error_type=error_type, provider="local_bin", details=details)


class LLMBinaryTimeoutError(LLMBinaryError):
    def __init__(self, message: str = "LLM binary timed out", *, timeout_s: float | None = None) -> None:
        details = {"timeout_s": timeout_s} if timeout_s is not None else None
        super().__init__(message, status_code=504, error_type="bin_timeout", details=details)


class LLMBinaryNonZeroExitError(LLMBinaryError):
    def __init__(
        self,
        message: str = "LLM binary exited with a non-zero status",
        *,
        exit_code: int | None = None,
        stderr: str | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if exit_code is not None:
            details["exit_code"] = exit_code
        if stderr:
            details["stderr"] = stderr
        super().__init__(message, status_code=502, error_type="bin_non_zero_exit", details=details)


class LLMBinaryOSFailure(LLMBinaryError):
    def __init__(self, message: str = "LLM binary failed to launch") -> None:
        super().__init__(message, status_code=502, error_type="bin_os_error")
