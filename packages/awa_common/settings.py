from __future__ import annotations

import os
import re
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Preserve legacy values while supporting new stage/dev env conventions.
EnvName = Literal["local", "test", "dev", "stage", "staging", "prod"]
AppRuntimeEnv = Literal["dev", "stage", "prod"]


def _default_env_file() -> str | None:
    # Prefer explicit ENV, fallback to .env.local for developers,
    # but allow containerized/CI to rely on real env vars.
    env = os.getenv("ENV", "local")
    if env == "local":
        return ".env.local" if os.path.exists(".env.local") else ".env"
    if env == "test":
        return ".env.test" if os.path.exists(".env.test") else None
    # staging/prod expected to use real env/secrets manager
    return None


_RATE_UNIT_SECONDS: dict[str, int] = {
    "second": 1,
    "sec": 1,
    "s": 1,
    "minute": 60,
    "min": 60,
    "m": 60,
}


def parse_rate_limit(limit: str) -> tuple[int, int]:
    """Parse a textual rate limit like ``\"30/min\"`` into (times, seconds)."""
    value = (limit or "").strip()
    if not value:
        raise ValueError("Rate limit value must be non-empty.")
    match = re.fullmatch(r"(?i)\s*(\d+)\s*/\s*([a-z]+)\s*", value)
    if not match:
        raise ValueError(f"Invalid rate limit format: {limit!r}")
    times = int(match.group(1))
    unit = match.group(2).lower()
    seconds = _RATE_UNIT_SECONDS.get(unit)
    if seconds is None:
        raise ValueError(f"Unsupported rate limit unit: {unit!r}")
    if times <= 0:
        raise ValueError("Rate limit count must be positive.")
    return times, seconds


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_default_env_file(), env_file_encoding="utf-8", extra="ignore")

    # Core
    ENV: str = "local"  # local|dev|stage|prod
    APP_NAME: str = "awa-app"
    APP_ENV: AppRuntimeEnv = "dev"
    APP_VERSION: str = "0.0.0"
    SERVICE_NAME: str = "api"

    # Database & cache
    DATABASE_URL: str = Field(default="postgresql+psycopg://app:app@db:5432/app")
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    BROKER_URL: str | None = None
    QUEUE_NAMES: str | None = None

    # Observability / security
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    SENTRY_DSN: str | None = None

    # Security headers / limits
    SECURITY_HSTS_ENABLED: bool = False
    SECURITY_REFERRER_POLICY: str = "strict-origin-when-cross-origin"
    SECURITY_FRAME_OPTIONS: str = "DENY"
    SECURITY_X_CONTENT_TYPE_OPTIONS: str = "nosniff"
    RATE_LIMIT_VIEWER: str = "30/minute"
    RATE_LIMIT_OPS: str = "120/minute"
    RATE_LIMIT_ADMIN: str = "240/minute"
    MAX_REQUEST_BYTES: int = 1_048_576  # 1 MB

    # Webapp
    NEXT_PUBLIC_API_URL: str = Field(default="http://localhost:8000")
    CORS_ORIGINS: str | None = None

    # Timeouts
    REQUEST_TIMEOUT_S: int = 15

    # ETL reliability defaults
    ETL_CONNECT_TIMEOUT_S: float = 5.0
    ETL_READ_TIMEOUT_S: float = 30.0
    ETL_TOTAL_TIMEOUT_S: float = 60.0
    ETL_MAX_RETRIES: int = 5
    ETL_BACKOFF_BASE_S: float = 0.5
    ETL_BACKOFF_MAX_S: float = 30.0
    ETL_RETRY_STATUS_CODES: list[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])

    # Optional: LLM placeholders (no usage change in this PR)
    LLM_PROVIDER: Literal["STUB", "OPENAI", "VLLM"] = "STUB"
    OPENAI_API_BASE: str | None = None
    OPENAI_API_KEY: str | None = None

    # Auth configuration (Keycloak OIDC)
    OIDC_ISSUER: str = Field(default="https://keycloak.local/realms/awa")
    OIDC_AUDIENCE: str = Field(default="awa-webapp")
    OIDC_JWKS_URL: str | None = None
    OIDC_JWKS_TTL_SECONDS: int = 900

    # Audit trail
    SECURITY_ENABLE_AUDIT: bool = True

    def redacted(self) -> dict:
        def _mask(url: str | None) -> str | None:
            if not url:
                return url
            # simple masking of credentials in URLs
            # e.g. postgresql+psycopg://user:pass@host:5432/db -> postgresql+psycopg://user:****@host:5432/db
            return re.sub(r"(://[^:/]+):[^@]+@", r"\1:****@", url)

        return {
            "ENV": self.ENV,
            "APP_NAME": self.APP_NAME,
            "APP_ENV": self.APP_ENV,
            "APP_VERSION": self.APP_VERSION,
            "SERVICE_NAME": self.SERVICE_NAME,
            "DATABASE_URL": _mask(self.DATABASE_URL),
            "REDIS_URL": _mask(self.REDIS_URL),
            "BROKER_URL": _mask(self.BROKER_URL),
            "SENTRY_DSN": "set" if bool(self.SENTRY_DSN) else None,
            "NEXT_PUBLIC_API_URL": self.NEXT_PUBLIC_API_URL,
            "CORS_ORIGINS": bool(self.CORS_ORIGINS),
            "LOG_LEVEL": self.LOG_LEVEL,
            "REQUEST_TIMEOUT_S": self.REQUEST_TIMEOUT_S,
            "LLM_PROVIDER": self.LLM_PROVIDER,
            "OPENAI_API_BASE": bool(self.OPENAI_API_BASE),
            "OPENAI_API_KEY": bool(self.OPENAI_API_KEY),
            "OIDC_ISSUER": self.OIDC_ISSUER,
            "QUEUE_NAMES": self.QUEUE_NAMES,
            "SECURITY_REFERRER_POLICY": self.SECURITY_REFERRER_POLICY,
            "SECURITY_FRAME_OPTIONS": self.SECURITY_FRAME_OPTIONS,
            "SECURITY_X_CONTENT_TYPE_OPTIONS": self.SECURITY_X_CONTENT_TYPE_OPTIONS,
            "SECURITY_HSTS_ENABLED": self.SECURITY_HSTS_ENABLED,
            "RATE_LIMIT_VIEWER": self.RATE_LIMIT_VIEWER,
            "RATE_LIMIT_OPS": self.RATE_LIMIT_OPS,
            "RATE_LIMIT_ADMIN": self.RATE_LIMIT_ADMIN,
            "MAX_REQUEST_BYTES": self.MAX_REQUEST_BYTES,
        }


settings = Settings()
