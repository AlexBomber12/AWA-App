from __future__ import annotations

import os
import re
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

from .dsn import build_dsn

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


def _ensure_asyncpg_dsn(url: str) -> str:
    """Normalize arbitrary Postgres URLs so they use the asyncpg driver."""
    try:
        parsed = make_url(url)
    except Exception:
        return url
    driver = parsed.drivername
    base, sep, suffix = driver.partition("+")
    if base in {"postgresql", "postgres"}:
        if sep:
            driver = f"{base}+asyncpg"
        else:
            driver = "postgresql+asyncpg"
        return str(parsed.set(drivername=driver))
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_default_env_file(), env_file_encoding="utf-8", extra="ignore")

    # Core
    ENV: str = "local"  # local|dev|stage|prod
    TESTING: bool = False
    APP_NAME: str = "awa-app"
    APP_ENV: AppRuntimeEnv = "dev"
    APP_VERSION: str = "0.0.0"
    SERVICE_NAME: str = "api"
    METRICS_TEXTFILE_DIR: str = ""
    METRICS_FLUSH_INTERVAL_S: float = 15.0

    # Database & cache
    DATABASE_URL: str = Field(default="postgresql+psycopg://app:app@db:5432/app")
    PG_ASYNC_DSN: str | None = None
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    BROKER_URL: str | None = Field(
        default=None,
        validation_alias=AliasChoices("BROKER_URL", "CELERY_BROKER_URL"),
    )
    QUEUE_NAMES: str | None = None
    SCHEDULE_MV_REFRESH: bool = True
    MV_REFRESH_CRON: str = "30 2 * * *"
    STATS_ENABLE_CACHE: bool = True
    STATS_CACHE_TTL_S: int = 600
    STATS_CACHE_NAMESPACE: str = "stats:"
    STATS_MAX_DAYS: int = 365
    REQUIRE_CLAMP: bool = False

    @property
    def POSTGRES_DSN(self) -> str:
        """Canonical async-friendly Postgres DSN."""
        candidates = (
            os.getenv("POSTGRES_DSN"),
            self.PG_ASYNC_DSN,
            self.DATABASE_URL,
        )
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return _ensure_asyncpg_dsn(candidate.strip())
        return build_dsn(sync=False)

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
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_SCORE_PER_USER: int = 8
    RATE_LIMIT_ROI_BY_VENDOR_PER_USER: int = 12
    MAX_REQUEST_BYTES: int = 268_435_456  # 256 MB ceiling for uploads
    INGEST_STREAMING_ENABLED: bool = True
    INGEST_CHUNK_SIZE_MB: int = 8
    S3_USE_AIOBOTO3: bool = True
    S3_MULTIPART_THRESHOLD_MB: int = 16
    S3_MAX_CONNECTIONS: int = 50
    SPOOL_MAX_BYTES: int = 67_108_864  # 64 MB safety cap for SpooledTemporaryFile
    ENABLE_LOOP_LAG_MONITOR: bool = False
    LOOP_LAG_INTERVAL_S: float = 1.0

    # Webapp
    NEXT_PUBLIC_API_URL: str = Field(default="http://localhost:8000")
    CORS_ORIGINS: str | None = None

    # Timeouts
    REQUEST_TIMEOUT_S: int = 15

    # ETL reliability defaults
    ETL_CONNECT_TIMEOUT_S: float = 5.0
    ETL_READ_TIMEOUT_S: float = 30.0
    ETL_TOTAL_TIMEOUT_S: float = 60.0
    ETL_POOL_TIMEOUT_S: float = Field(
        default=5.0,
        validation_alias=AliasChoices("ETL_POOL_TIMEOUT_S", "ETL_HTTP_POOL_QUEUE_TIMEOUT_S"),
    )
    ETL_HTTP_KEEPALIVE: int = Field(
        default=5,
        validation_alias=AliasChoices("ETL_HTTP_KEEPALIVE", "ETL_HTTP_KEEPALIVE_CONNECTIONS"),
    )
    ETL_HTTP_MAX_CONNECTIONS: int = 20
    ETL_RETRY_ATTEMPTS: int = Field(
        default=5,
        validation_alias=AliasChoices("ETL_RETRY_ATTEMPTS", "ETL_MAX_RETRIES"),
    )
    ETL_RETRY_BASE_S: float = Field(
        default=0.5,
        validation_alias=AliasChoices("ETL_RETRY_BASE_S", "ETL_BACKOFF_BASE_S"),
    )
    ETL_RETRY_MIN_S: float = 0.5
    ETL_RETRY_MAX_S: float = Field(
        default=30.0,
        validation_alias=AliasChoices("ETL_RETRY_MAX_S", "ETL_BACKOFF_MAX_S"),
    )
    ETL_RETRY_JITTER_S: float = 1.0
    ETL_RETRY_STATUS_CODES: list[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])

    # Optional: LLM placeholders (no usage change in this PR)
    LLM_PROVIDER: Literal["STUB", "OPENAI", "VLLM"] = "STUB"
    OPENAI_API_BASE: str | None = None
    OPENAI_API_KEY: str | None = None
    LLM_REQUEST_TIMEOUT_S: float = 60.0

    # Auth configuration (Keycloak OIDC)
    OIDC_ISSUER: str = Field(default="https://keycloak.local/realms/awa")
    OIDC_AUDIENCE: str = Field(default="awa-webapp")
    OIDC_JWKS_URL: str | None = None
    OIDC_JWKS_TTL_SECONDS: int = 300
    OIDC_JWKS_STALE_GRACE_SECONDS: int = 120
    OIDC_JWKS_TIMEOUT_CONNECT_S: float = 2.0
    OIDC_JWKS_TIMEOUT_READ_S: float = 2.0
    OIDC_JWKS_TIMEOUT_TOTAL_S: float = 5.0
    OIDC_JWKS_POOL_LIMIT: int = 8
    OIDC_JWKS_BACKGROUND_REFRESH: bool = True

    # Audit trail
    SECURITY_ENABLE_AUDIT: bool = True

    # Alert bot configuration
    TELEGRAM_TOKEN: str = ""
    TELEGRAM_DEFAULT_CHAT_ID: int | str | None = Field(
        default=None,
        validation_alias=AliasChoices("TELEGRAM_DEFAULT_CHAT_ID", "TELEGRAM_CHAT_ID"),
    )
    TELEGRAM_API_BASE: str = "https://api.telegram.org"
    ALERTS_ENABLED: bool = Field(
        default=True,
        validation_alias=AliasChoices("ALERTS_ENABLED", "ENABLE_ALERTS"),
    )
    ALERT_RULES_SOURCE: Literal["yaml", "db"] = "yaml"
    ALERT_RULES_FILE: str = "config/alert_rules.yaml"
    ALERT_RULES_PATH: str = "services/alert_bot/config.yaml"
    ALERT_RULES_WATCH: bool = False
    ALERT_RULES_WATCH_INTERVAL_S: float = 60.0
    ALERT_RULES_OVERRIDE: str | None = None
    ALERTS_EVALUATION_INTERVAL_CRON: str = Field(
        default="*/5 * * * *",
        validation_alias=AliasChoices("ALERTS_EVALUATION_INTERVAL_CRON", "ALERTS_CRON"),
    )
    ALERT_SCHEDULE_CRON: str = "*/1 * * * *"
    ALERT_EVAL_CONCURRENCY: int = 8
    ALERT_SEND_CONCURRENCY: int = 8
    ALERT_TELEGRAM_MAX_RPS: float = 25.0
    ALERT_TELEGRAM_MAX_CHAT_RPS: float = 1.0
    ALERT_RULE_TIMEOUT_S: float = 15.0
    TELEGRAM_CONNECT_TIMEOUT_S: float = 3.0
    TELEGRAM_TOTAL_TIMEOUT_S: float = 10.0
    ROI_THRESHOLD: int = 5
    ROI_DURATION_DAYS: int = 30
    COST_DELTA_PCT: int = 10
    PRICE_DROP_PCT: int = 15
    RETURNS_PCT: int = 5
    STALE_DAYS: int = 30
    ALERT_DB_POOL_MIN_SIZE: int = 1
    ALERT_DB_POOL_MAX_SIZE: int = 5
    ALERT_DB_POOL_TIMEOUT: float = 10.0
    ALERT_DB_POOL_ACQUIRE_TIMEOUT: float = 3.0
    ALERT_DB_POOL_ACQUIRE_RETRIES: int = 3
    ALERT_DB_POOL_RETRY_DELAY: float = 0.25

    # Async DB pools (FastAPI & workers)
    ASYNC_DB_POOL_SIZE: int = 10
    ASYNC_DB_MAX_OVERFLOW: int = 10
    ASYNC_DB_POOL_TIMEOUT: float = 30.0
    DB_STATEMENT_TIMEOUT_SECONDS: int = 30

    # Logistics ETL configuration
    LOGISTICS_TIMEOUT_S: float = 15.0
    LOGISTICS_RETRIES: int = 3
    LOGISTICS_SOURCES: str | None = None
    FREIGHT_API_URL: str = "https://example.com/freight.csv"
    LOGISTICS_MAX_CONCURRENCY: int = 6
    LOGISTICS_PER_SOURCE_TIMEOUT_SECONDS: int = 60
    LOGISTICS_GATHER_TIMEOUT_SECONDS: int = 120
    LOGISTICS_UPSERT_BATCH_SIZE: int = 20_000

    # Fees ingestion / external APIs
    HELIUM10_KEY: str | None = None
    FEES_RAW_TABLE: str = "fees_raw"
    H10_MAX_CONCURRENCY: int = 5
    H10_DB_POOL_MAX_SIZE: int = 10

    # Price importer
    PRICE_IMPORTER_CHUNK_ROWS: int = 10_000
    PRICE_IMPORTER_VALIDATION_WORKERS: int = 4

    @property
    def ETL_HTTP_KEEPALIVE_CONNECTIONS(self) -> int:  # pragma: no cover - compatibility shim
        return self.ETL_HTTP_KEEPALIVE

    @property
    def ETL_HTTP_POOL_QUEUE_TIMEOUT_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.ETL_POOL_TIMEOUT_S

    @property
    def ETL_MAX_RETRIES(self) -> int:  # pragma: no cover - compatibility shim
        return self.ETL_RETRY_ATTEMPTS

    @property
    def ETL_BACKOFF_BASE_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.ETL_RETRY_BASE_S

    @property
    def ETL_BACKOFF_MAX_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.ETL_RETRY_MAX_S

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
            "VERSION": self.VERSION,
            "SERVICE_NAME": self.SERVICE_NAME,
            "DATABASE_URL": _mask(self.DATABASE_URL),
            "PG_ASYNC_DSN": _mask(self.PG_ASYNC_DSN),
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
            "TELEGRAM_TOKEN": bool(self.TELEGRAM_TOKEN),
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
            "HELIUM10_KEY": bool(self.HELIUM10_KEY),
            "METRICS_TEXTFILE_DIR": bool(self.METRICS_TEXTFILE_DIR),
            "METRICS_FLUSH_INTERVAL_S": self.METRICS_FLUSH_INTERVAL_S,
        }

    @property
    def TELEGRAM_CHAT_ID(self) -> int | str | None:  # pragma: no cover - compatibility shim
        return self.TELEGRAM_DEFAULT_CHAT_ID

    @property
    def VERSION(self) -> str:
        for candidate in (
            getattr(self, "APP_VERSION", None),
            os.getenv("VERSION"),
            os.getenv("GIT_SHA"),
            os.getenv("COMMIT_SHA"),
        ):
            value = (candidate or "").strip() if isinstance(candidate, str) else candidate
            if value:
                return str(value)
        return "0.0.0"


settings: Settings = Settings()
