from __future__ import annotations

import json
import logging
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

    # Auth configuration
    AUTH_MODE: Literal["disabled", "oidc", "forward-auth"] = "disabled"
    OIDC_ISSUER: str | None = None
    OIDC_AUDIENCE: str | None = None
    OIDC_CLIENT_ID: str | None = None
    OIDC_JWKS_URL: str | None = None
    OIDC_ALGS: str = "RS256"
    FA_USER_HEADER: str = "X-Forwarded-User"
    FA_EMAIL_HEADER: str = "X-Forwarded-Email"
    FA_GROUPS_HEADER: str = "X-Forwarded-Groups"
    ROLE_MAP_JSON: str = '{"admin":["admin"],"ops":["ops"],"viewer":["viewer"]}'
    AUTH_REQUIRED_ROUTES_REGEX: str = ""

    _role_map_cache: dict[str, set[str]] | None = None
    _role_map_cache_key: str | None = None
    _role_regex_cache: re.Pattern[str] | None = None
    _role_regex_cache_key: str | None = None

    def _load_role_map(self) -> dict[str, set[str]]:
        raw_json = self.ROLE_MAP_JSON or "{}"
        if self._role_map_cache is not None and self._role_map_cache_key == raw_json:
            return self._role_map_cache
        try:
            raw = json.loads(raw_json)
        except json.JSONDecodeError:
            raw = {}
        mapping: dict[str, set[str]] = {}
        for internal_role, external_values in raw.items():
            if not isinstance(internal_role, str):
                continue
            values: set[str] = set()
            if isinstance(external_values, (list, tuple, set)):
                values = {str(value) for value in external_values}
            elif isinstance(external_values, str):
                values = {external_values}
            mapping[internal_role] = values
        self._role_map_cache = mapping
        self._role_map_cache_key = raw_json
        return self._role_map_cache

    def resolve_role_set(self, claims_or_groups: set[str]) -> set[str]:
        """Map external IdP/forward-auth groups into internal role names."""
        if not claims_or_groups:
            claims_or_groups = set()
        mapping = self._load_role_map()
        resolved = {
            role for role, external in mapping.items() if external & claims_or_groups
        }
        # Allow explicit passthrough: if internal role directly referenced externally.
        direct = {role for role in mapping if role in claims_or_groups}
        resolved.update(direct)
        return resolved

    def configured_roles(self) -> set[str]:
        """Return all internal roles declared in ROLE_MAP_JSON."""
        return set(self._load_role_map().keys())

    def should_protect_path(self, path: str) -> bool:
        regex = (self.AUTH_REQUIRED_ROUTES_REGEX or "").strip()
        if not regex:
            return False
        if self._role_regex_cache is None or self._role_regex_cache_key != regex:
            try:
                compiled = re.compile(regex)
            except re.error:
                logging.getLogger(__name__).warning(
                    "Invalid AUTH_REQUIRED_ROUTES_REGEX=%r — failing closed (protect all)",
                    regex,
                )
                compiled = re.compile(".*")
            self._role_regex_cache = compiled
            self._role_regex_cache_key = regex
        return bool(self._role_regex_cache.search(path))

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
            "AUTH_MODE": self.AUTH_MODE,
        }


settings = Settings()
