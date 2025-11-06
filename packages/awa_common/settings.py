from __future__ import annotations

import os
import re
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvName = Literal["local", "test", "staging", "prod"]


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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_default_env_file(), env_file_encoding="utf-8", extra="ignore"
    )

    # Core
    ENV: EnvName = "local"
    APP_NAME: str = "awa-app"

    # Database & cache
    DATABASE_URL: str = Field(default="postgresql+psycopg://app:app@db:5432/app")
    REDIS_URL: str = Field(default="redis://redis:6379/0")

    # Observability / security
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    SENTRY_DSN: str | None = None

    # Webapp
    NEXT_PUBLIC_API_URL: str = Field(default="http://localhost:8000")

    # Timeouts
    REQUEST_TIMEOUT_S: int = 15

    # Optional: LLM placeholders (no usage change in this PR)
    LLM_PROVIDER: Literal["STUB", "OPENAI", "VLLM"] = "STUB"
    OPENAI_API_BASE: str | None = None
    OPENAI_API_KEY: str | None = None

    # Auth configuration (Keycloak OIDC)
    OIDC_ISSUER: str = Field(default="https://keycloak.local/realms/awa")
    OIDC_AUDIENCE: str = Field(default="awa-webapp")
    OIDC_JWKS_URL: str | None = None
    OIDC_JWKS_TTL_SECONDS: int = 900

    # Per-role rate limiting windows
    RATE_LIMIT_VIEWER_TIMES: int = 60
    RATE_LIMIT_VIEWER_SECONDS: int = 60
    RATE_LIMIT_OPS_TIMES: int = 120
    RATE_LIMIT_OPS_SECONDS: int = 60
    RATE_LIMIT_ADMIN_TIMES: int = 180
    RATE_LIMIT_ADMIN_SECONDS: int = 60

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
            "DATABASE_URL": _mask(self.DATABASE_URL),
            "REDIS_URL": _mask(self.REDIS_URL),
            "SENTRY_DSN": "set" if bool(self.SENTRY_DSN) else None,
            "NEXT_PUBLIC_API_URL": self.NEXT_PUBLIC_API_URL,
            "LOG_LEVEL": self.LOG_LEVEL,
            "REQUEST_TIMEOUT_S": self.REQUEST_TIMEOUT_S,
            "LLM_PROVIDER": self.LLM_PROVIDER,
            "OPENAI_API_BASE": bool(self.OPENAI_API_BASE),
            "OPENAI_API_KEY": bool(self.OPENAI_API_KEY),
            "OIDC_ISSUER": self.OIDC_ISSUER,
        }


settings = Settings()
