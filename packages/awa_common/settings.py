from __future__ import annotations

import os
import re
from decimal import Decimal
from functools import cached_property
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

from .configuration import (
    AlertSettings,
    AppSettings,
    CelerySettings,
    DatabaseSettings,
    EmailSettings,
    EtlSettings,
    LLMSettings,
    MaintenanceSettings,
    ObservabilitySettings,
    RedisSettings,
    RepricerSettings,
    RoiSettings,
    S3Settings,
    SecuritySettings,
    StatsSettings,
)
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
    ALEMBIC_CONFIG: str = "services/api/alembic.ini"
    WAIT_FOR_DB_MAX_ATTEMPTS: int | None = None
    WAIT_FOR_DB_DELAY_S: float | None = None

    # Database & cache
    DATABASE_URL: str = Field(default="postgresql+psycopg://app:app@db:5432/app")
    PG_ASYNC_DSN: str | None = None
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    CACHE_REDIS_URL: str | None = None
    CACHE_DEFAULT_TTL_S: int = 300
    CACHE_NAMESPACE: str = "cache:"
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
    STATS_USE_SQL: bool = False
    REQUIRE_CLAMP: bool = False
    REDIS_HEALTH_CRITICAL: bool = False
    RETURNS_STATS_VIEW_NAME: str = "returns_raw"
    ROI_VIEW_NAME: str = "v_roi_full"
    ROI_MATERIALIZED_VIEW_NAME: str = "mat_v_roi_full"

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
    SENTRY_TRACES_SAMPLE_RATE: float = 0.05
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.0
    ENABLE_METRICS: bool = True
    PROMETHEUS_MULTIPROC_DIR: str | None = None
    WORKER_METRICS_HTTP: bool = False
    WORKER_METRICS_PORT: int = 9108

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
    INGEST_STREAMING_CHUNK_SIZE: int = 50_000
    INGEST_IDEMPOTENT: bool = True
    ANALYZE_MIN_ROWS: int = 50_000
    USE_COPY: bool = True
    S3_USE_AIOBOTO3: bool = True
    S3_MULTIPART_THRESHOLD_MB: int = 16
    S3_MAX_CONNECTIONS: int = 50
    SPOOL_MAX_BYTES: int = 67_108_864  # 64 MB safety cap for SpooledTemporaryFile
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_SECURE: bool = False
    MINIO_ACCESS_KEY: str = "minio"
    MINIO_SECRET_KEY: str = "minio123"
    MINIO_BUCKET: str = "awa-bucket"
    AWS_REGION: str = "us-east-1"
    ENABLE_LOOP_LAG_MONITOR: bool = False
    LOOP_LAG_INTERVAL_S: float = 1.0
    HEALTHCHECK_DB_TIMEOUT_S: float = 2.0
    HEALTHCHECK_REDIS_SOCKET_TIMEOUT_S: float = 2.0
    HEALTHCHECK_HTTP_TIMEOUT_S: float = 2.0
    HEALTHCHECK_CELERY_TIMEOUT_S: float = 2.0
    HEALTHCHECK_INSPECT_TIMEOUT_S: float = 1.0
    HEALTHCHECK_RETRY_ATTEMPTS: int = 3
    HEALTHCHECK_RETRY_DELAY_S: float = 1.0

    # Webapp
    NEXT_PUBLIC_API_URL: str = Field(default="http://localhost:8000")
    CORS_ORIGINS: str | None = None

    # Timeouts
    REQUEST_TIMEOUT_S: int = 15

    # Celery / worker
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_TASK_TIME_LIMIT: int = 3600
    CELERY_TASK_STORE_EAGER_RESULT: bool = False
    CELERY_RESULT_EXPIRES: int = 86_400
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_LOOP_LAG_MONITOR: bool = True
    CELERY_LOOP_LAG_INTERVAL_S: float | None = None
    BACKLOG_PROBE_SECONDS: int = 15
    SCHEDULE_NIGHTLY_MAINTENANCE: bool = True
    NIGHTLY_MAINTENANCE_CRON: str = "30 2 * * *"
    SCHEDULE_LOGISTICS_ETL: bool = False
    LOGISTICS_CRON: str = "0 3 * * *"
    CHECK_INTERVAL_MIN: int | None = None
    TZ: str = "UTC"

    # Shared HTTP client defaults
    HTTP_CONNECT_TIMEOUT_S: float = Field(
        default=5.0,
        validation_alias=AliasChoices("HTTP_CONNECT_TIMEOUT_S", "ETL_CONNECT_TIMEOUT_S"),
    )
    HTTP_READ_TIMEOUT_S: float = Field(
        default=30.0,
        validation_alias=AliasChoices("HTTP_READ_TIMEOUT_S", "ETL_READ_TIMEOUT_S"),
    )
    HTTP_TOTAL_TIMEOUT_S: float = Field(
        default=60.0,
        validation_alias=AliasChoices("HTTP_TOTAL_TIMEOUT_S", "ETL_TOTAL_TIMEOUT_S"),
    )
    HTTP_POOL_TIMEOUT_S: float = Field(
        default=5.0,
        validation_alias=AliasChoices("HTTP_POOL_TIMEOUT_S", "ETL_POOL_TIMEOUT_S", "ETL_HTTP_POOL_QUEUE_TIMEOUT_S"),
    )
    HTTP_MAX_CONNECTIONS: int = Field(
        default=20,
        validation_alias=AliasChoices("HTTP_MAX_CONNECTIONS", "ETL_HTTP_MAX_CONNECTIONS"),
    )
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = Field(
        default=5,
        validation_alias=AliasChoices(
            "HTTP_MAX_KEEPALIVE_CONNECTIONS", "ETL_HTTP_KEEPALIVE", "ETL_HTTP_KEEPALIVE_CONNECTIONS"
        ),
    )
    HTTP_MAX_RETRIES: int = Field(
        default=5,
        validation_alias=AliasChoices("HTTP_MAX_RETRIES", "ETL_RETRY_ATTEMPTS", "ETL_MAX_RETRIES"),
    )
    HTTP_BACKOFF_BASE_S: float = Field(
        default=0.5,
        validation_alias=AliasChoices("HTTP_BACKOFF_BASE_S", "ETL_RETRY_BASE_S", "ETL_BACKOFF_BASE_S"),
    )
    HTTP_BACKOFF_MAX_S: float = Field(
        default=30.0,
        validation_alias=AliasChoices("HTTP_BACKOFF_MAX_S", "ETL_RETRY_MAX_S", "ETL_BACKOFF_MAX_S"),
    )
    HTTP_BACKOFF_JITTER_S: float = Field(
        default=1.0,
        validation_alias=AliasChoices("HTTP_BACKOFF_JITTER_S", "ETL_RETRY_JITTER_S"),
    )
    HTTP_RETRY_STATUS_CODES: list[int] = Field(
        default_factory=lambda: [429, 500, 502, 503, 504],
        validation_alias=AliasChoices("HTTP_RETRY_STATUS_CODES", "ETL_RETRY_STATUS_CODES"),
    )
    ETL_RETRY_MIN_S: float = 0.5
    ENABLE_LIVE: bool = False
    TASK_ID: str | None = None
    HELIUM_API_KEY: str | None = None
    KEEPA_KEY: str | None = None
    REGION: str = "US"
    SP_FEES_DATE: str | None = None
    SP_REFRESH_TOKEN: str | None = None
    SP_CLIENT_ID: str | None = None
    SP_CLIENT_SECRET: str | None = None
    SP_API_BASE_URL: str | None = None

    # Optional: LLM placeholders (no usage change in this PR)
    LLM_PROVIDER: str = Field(default="STUB")
    LLM_PROVIDER_FALLBACK: str = "stub"
    LLM_URL: str = "http://llm:8000/llm"
    LLM_REMOTE_URL: str | None = None
    LLM_BASE_URL: str = Field(default="http://localhost:8000", validation_alias=AliasChoices("LLM_BASE_URL"))
    LAN_BASE_URL: str = Field(default="http://lan-llm:8000", validation_alias=AliasChoices("LAN_BASE"))
    LLM_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_API_BASE: str | None = None
    OPENAI_API_KEY: str | None = None
    LLM_REQUEST_TIMEOUT_S: float = Field(
        default=60.0,
        validation_alias=AliasChoices("LLM_REQUEST_TIMEOUT_S", "LLM_TIMEOUT_SECS"),
    )
    LLM_LAN_HEALTH_TIMEOUT_S: float = 1.0

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
    TABLE_MAINTENANCE_LIST: str = "public.reimbursements_raw,public.returns_raw"
    VACUUM_ENABLE: bool = False

    # Fees ingestion / external APIs
    HELIUM10_KEY: str | None = None
    FEES_RAW_TABLE: str = "fees_raw"
    H10_MAX_CONCURRENCY: int = 5
    H10_DB_POOL_MAX_SIZE: int = 10

    # Price importer
    PRICE_IMPORTER_CHUNK_ROWS: int = 10_000
    PRICE_IMPORTER_VALIDATION_WORKERS: int = 4

    # Email ingestion
    IMAP_HOST: str = ""
    IMAP_USER: str = ""
    IMAP_PASS: str = ""

    # Repricer defaults
    REPRICER_MIN_ROI: Decimal = Decimal("0.05")
    REPRICER_BUYBOX_GAP: Decimal = Decimal("0.05")
    REPRICER_ROUND: Decimal = Decimal("0.10")

    @cached_property
    def app(self) -> AppSettings:
        return AppSettings.from_settings(self)

    @cached_property
    def db(self) -> DatabaseSettings:
        return DatabaseSettings.from_settings(self)

    @cached_property
    def redis(self) -> RedisSettings:
        return RedisSettings.from_settings(self)

    @cached_property
    def s3(self) -> S3Settings:
        return S3Settings.from_settings(self)

    @cached_property
    def celery(self) -> CelerySettings:
        return CelerySettings.from_settings(self)

    @cached_property
    def security(self) -> SecuritySettings:
        return SecuritySettings.from_settings(self)

    @cached_property
    def observability(self) -> ObservabilitySettings:
        return ObservabilitySettings.from_settings(self)

    @cached_property
    def llm(self) -> LLMSettings:
        return LLMSettings.from_settings(self)

    @cached_property
    def stats(self) -> StatsSettings:
        return StatsSettings.from_settings(self)

    @cached_property
    def alerts(self) -> AlertSettings:
        return AlertSettings.from_settings(self)

    @cached_property
    def etl(self) -> EtlSettings:
        return EtlSettings.from_settings(self)

    @cached_property
    def maintenance(self) -> MaintenanceSettings:
        return MaintenanceSettings.from_settings(self)

    @cached_property
    def email(self) -> EmailSettings:
        return EmailSettings.from_settings(self)

    @cached_property
    def repricer(self) -> RepricerSettings:
        return RepricerSettings.from_settings(self)

    @cached_property
    def roi(self) -> RoiSettings:
        return RoiSettings.from_settings(self)

    @property
    def wait_for_db_max_attempts(self) -> int:
        env = (self.ENV or "local").strip().lower()
        default = 10 if env in {"local", "test"} else 50
        return int(self.WAIT_FOR_DB_MAX_ATTEMPTS or default)

    @property
    def wait_for_db_delay_s(self) -> float:
        env = (self.ENV or "local").strip().lower()
        default = 0.05 if env in {"local", "test"} else 0.2
        return float(self.WAIT_FOR_DB_DELAY_S or default)

    @property
    def ETL_CONNECT_TIMEOUT_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.HTTP_CONNECT_TIMEOUT_S

    @property
    def ETL_READ_TIMEOUT_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.HTTP_READ_TIMEOUT_S

    @property
    def ETL_TOTAL_TIMEOUT_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.HTTP_TOTAL_TIMEOUT_S

    @property
    def ETL_POOL_TIMEOUT_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.HTTP_POOL_TIMEOUT_S

    @property
    def ETL_HTTP_KEEPALIVE(self) -> int:  # pragma: no cover - compatibility shim
        return self.HTTP_MAX_KEEPALIVE_CONNECTIONS

    @property
    def ETL_HTTP_KEEPALIVE_CONNECTIONS(self) -> int:  # pragma: no cover - compatibility shim
        return self.HTTP_MAX_KEEPALIVE_CONNECTIONS

    @property
    def ETL_HTTP_POOL_QUEUE_TIMEOUT_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.HTTP_POOL_TIMEOUT_S

    @property
    def ETL_HTTP_MAX_CONNECTIONS(self) -> int:  # pragma: no cover - compatibility shim
        return self.HTTP_MAX_CONNECTIONS

    @property
    def ETL_MAX_RETRIES(self) -> int:  # pragma: no cover - compatibility shim
        return self.HTTP_MAX_RETRIES

    @property
    def ETL_RETRY_ATTEMPTS(self) -> int:  # pragma: no cover - compatibility shim
        return self.HTTP_MAX_RETRIES

    @property
    def ETL_RETRY_BASE_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.HTTP_BACKOFF_BASE_S

    @property
    def ETL_BACKOFF_BASE_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.HTTP_BACKOFF_BASE_S

    @property
    def ETL_RETRY_MAX_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.HTTP_BACKOFF_MAX_S

    @property
    def ETL_BACKOFF_MAX_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.HTTP_BACKOFF_MAX_S

    @property
    def ETL_RETRY_JITTER_S(self) -> float:  # pragma: no cover - compatibility shim
        return self.HTTP_BACKOFF_JITTER_S

    @property
    def ETL_RETRY_STATUS_CODES(self) -> list[int]:  # pragma: no cover - compatibility shim
        return list(self.HTTP_RETRY_STATUS_CODES)

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
