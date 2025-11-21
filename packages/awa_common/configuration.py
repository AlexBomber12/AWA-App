from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:  # pragma: no cover
    from .settings import Settings


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return list(value)


class SettingsGroup(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class AppSettings(SettingsGroup):
    env: str
    runtime_env: str
    testing: bool
    name: str
    service_name: str
    version: str
    config_path: str
    request_timeout_s: int
    wait_for_db_max_attempts: int
    wait_for_db_delay_s: float

    @property
    def is_local(self) -> bool:
        return self.env in {"local", "test"}

    @classmethod
    def from_settings(cls, cfg: Settings) -> AppSettings:
        return cls(
            env=cfg.ENV,
            runtime_env=cfg.APP_ENV,
            testing=cfg.TESTING,
            name=cfg.APP_NAME,
            service_name=cfg.SERVICE_NAME,
            version=cfg.VERSION,
            config_path=cfg.ALEMBIC_CONFIG,
            request_timeout_s=int(cfg.REQUEST_TIMEOUT_S),
            wait_for_db_max_attempts=cfg.wait_for_db_max_attempts,
            wait_for_db_delay_s=cfg.wait_for_db_delay_s,
        )


class DatabaseSettings(SettingsGroup):
    url: str
    async_dsn: str
    pool_size: int
    max_overflow: int
    pool_timeout: float
    statement_timeout_seconds: int
    alert_pool_min_size: int
    alert_pool_max_size: int
    alert_pool_timeout: float
    alert_pool_acquire_timeout: float
    alert_pool_acquire_retries: int
    alert_pool_retry_delay: float

    @classmethod
    def from_settings(cls, cfg: Settings) -> DatabaseSettings:
        return cls(
            url=cfg.DATABASE_URL,
            async_dsn=cfg.POSTGRES_DSN,
            pool_size=int(cfg.ASYNC_DB_POOL_SIZE),
            max_overflow=int(cfg.ASYNC_DB_MAX_OVERFLOW),
            pool_timeout=float(cfg.ASYNC_DB_POOL_TIMEOUT),
            statement_timeout_seconds=int(cfg.DB_STATEMENT_TIMEOUT_SECONDS),
            alert_pool_min_size=int(cfg.ALERT_DB_POOL_MIN_SIZE),
            alert_pool_max_size=int(cfg.ALERT_DB_POOL_MAX_SIZE),
            alert_pool_timeout=float(cfg.ALERT_DB_POOL_TIMEOUT),
            alert_pool_acquire_timeout=float(cfg.ALERT_DB_POOL_ACQUIRE_TIMEOUT),
            alert_pool_acquire_retries=int(cfg.ALERT_DB_POOL_ACQUIRE_RETRIES),
            alert_pool_retry_delay=float(cfg.ALERT_DB_POOL_RETRY_DELAY),
        )


class RedisSettings(SettingsGroup):
    url: str
    broker_url: str
    queue_names: list[str]
    health_critical: bool

    @classmethod
    def from_settings(cls, cfg: Settings) -> RedisSettings:
        broker = cfg.BROKER_URL or cfg.REDIS_URL
        return cls(
            url=cfg.REDIS_URL,
            broker_url=broker,
            queue_names=_split_csv(cfg.QUEUE_NAMES),
            health_critical=bool(cfg.REDIS_HEALTH_CRITICAL),
        )


class S3Settings(SettingsGroup):
    endpoint: str
    secure: bool
    access_key: str
    secret_key: str
    region: str
    bucket: str
    use_aioboto3: bool
    multipart_threshold_mb: int
    max_connections: int
    spool_max_bytes: int

    @classmethod
    def from_settings(cls, cfg: Settings) -> S3Settings:
        return cls(
            endpoint=cfg.MINIO_ENDPOINT,
            secure=bool(cfg.MINIO_SECURE),
            access_key=cfg.MINIO_ACCESS_KEY,
            secret_key=cfg.MINIO_SECRET_KEY,
            region=cfg.AWS_REGION,
            bucket=cfg.MINIO_BUCKET,
            use_aioboto3=bool(cfg.S3_USE_AIOBOTO3),
            multipart_threshold_mb=int(cfg.S3_MULTIPART_THRESHOLD_MB),
            max_connections=int(cfg.S3_MAX_CONNECTIONS),
            spool_max_bytes=int(cfg.SPOOL_MAX_BYTES),
        )

    def endpoint_url(self, *, secure_override: bool | None = None) -> str:
        secure = self.secure if secure_override is None else bool(secure_override)
        endpoint = (self.endpoint or "").strip()
        if "://" in endpoint:
            return endpoint
        scheme = "https" if secure else "http"
        return f"{scheme}://{endpoint}"

    def client_kwargs(self, *, secure_override: bool | None = None) -> dict[str, Any]:
        return {
            "endpoint_url": self.endpoint_url(secure_override=secure_override),
            "aws_access_key_id": self.access_key,
            "aws_secret_access_key": self.secret_key,
            "region_name": self.region,
        }


class CelerySettings(SettingsGroup):
    broker_url: str
    result_backend: str
    prefetch_multiplier: int
    task_time_limit: int
    store_eager_result: bool
    result_expires: int
    timezone: str
    always_eager: bool
    loop_lag_monitor_enabled: bool
    loop_lag_interval_s: float
    enable_metrics: bool
    backlog_probe_seconds: int
    schedule_nightly_maintenance: bool
    nightly_maintenance_cron: str
    schedule_mv_refresh: bool
    mv_refresh_cron: str
    schedule_logistics_etl: bool
    logistics_cron: str
    alerts_schedule_cron: str
    alerts_check_interval_min: int | None

    @classmethod
    def from_settings(cls, cfg: Settings) -> CelerySettings:
        redis = cfg.REDIS_URL
        return cls(
            broker_url=cfg.BROKER_URL or redis,
            result_backend=cfg.RESULT_BACKEND or redis,
            prefetch_multiplier=int(cfg.CELERY_WORKER_PREFETCH_MULTIPLIER),
            task_time_limit=int(cfg.CELERY_TASK_TIME_LIMIT),
            store_eager_result=bool(cfg.CELERY_TASK_STORE_EAGER_RESULT),
            result_expires=int(cfg.CELERY_RESULT_EXPIRES),
            timezone=cfg.TZ,
            always_eager=bool(cfg.CELERY_TASK_ALWAYS_EAGER),
            loop_lag_monitor_enabled=bool(cfg.CELERY_LOOP_LAG_MONITOR),
            loop_lag_interval_s=float(cfg.CELERY_LOOP_LAG_INTERVAL_S or cfg.LOOP_LAG_INTERVAL_S),
            enable_metrics=bool(cfg.ENABLE_METRICS),
            backlog_probe_seconds=int(cfg.BACKLOG_PROBE_SECONDS),
            schedule_nightly_maintenance=bool(cfg.SCHEDULE_NIGHTLY_MAINTENANCE),
            nightly_maintenance_cron=cfg.NIGHTLY_MAINTENANCE_CRON,
            schedule_mv_refresh=bool(cfg.SCHEDULE_MV_REFRESH),
            mv_refresh_cron=cfg.MV_REFRESH_CRON,
            schedule_logistics_etl=bool(cfg.SCHEDULE_LOGISTICS_ETL),
            logistics_cron=cfg.LOGISTICS_CRON,
            alerts_schedule_cron=cfg.ALERTS_EVALUATION_INTERVAL_CRON,
            alerts_check_interval_min=int(cfg.CHECK_INTERVAL_MIN) if cfg.CHECK_INTERVAL_MIN else None,
        )

    @property
    def alertbot_cron(self) -> str:
        """Return the effective alert bot cadence derived from validated settings."""

        if self.alerts_check_interval_min is not None:
            minutes = max(1, int(self.alerts_check_interval_min))
            return f"*/{minutes} * * * *"
        return self.alerts_schedule_cron


class SecuritySettings(SettingsGroup):
    max_request_bytes: int
    cors_origins: list[str]
    hsts_enabled: bool
    referrer_policy: str
    frame_options: str
    x_content_type_options: str
    oidc_issuer: str
    oidc_audience: str
    oidc_jwks_url: str | None
    oidc_jwks_ttl_seconds: int
    oidc_jwks_stale_grace_seconds: int
    oidc_jwks_timeout_connect_s: float
    oidc_jwks_timeout_read_s: float
    oidc_jwks_timeout_total_s: float
    oidc_jwks_pool_limit: int
    oidc_jwks_background_refresh: bool
    rate_limit_viewer: str
    rate_limit_ops: str
    rate_limit_admin: str
    rate_limit_window_seconds: int
    rate_limit_score_per_user: int
    rate_limit_roi_by_vendor_per_user: int
    audit_enabled: bool

    @classmethod
    def from_settings(cls, cfg: Settings) -> SecuritySettings:
        return cls(
            max_request_bytes=int(cfg.MAX_REQUEST_BYTES),
            cors_origins=_split_csv(cfg.CORS_ORIGINS),
            hsts_enabled=bool(cfg.SECURITY_HSTS_ENABLED),
            referrer_policy=cfg.SECURITY_REFERRER_POLICY,
            frame_options=cfg.SECURITY_FRAME_OPTIONS,
            x_content_type_options=cfg.SECURITY_X_CONTENT_TYPE_OPTIONS,
            oidc_issuer=cfg.OIDC_ISSUER,
            oidc_audience=cfg.OIDC_AUDIENCE,
            oidc_jwks_url=cfg.OIDC_JWKS_URL,
            oidc_jwks_ttl_seconds=int(cfg.OIDC_JWKS_TTL_SECONDS),
            oidc_jwks_stale_grace_seconds=int(cfg.OIDC_JWKS_STALE_GRACE_SECONDS),
            oidc_jwks_timeout_connect_s=float(cfg.OIDC_JWKS_TIMEOUT_CONNECT_S),
            oidc_jwks_timeout_read_s=float(cfg.OIDC_JWKS_TIMEOUT_READ_S),
            oidc_jwks_timeout_total_s=float(cfg.OIDC_JWKS_TIMEOUT_TOTAL_S),
            oidc_jwks_pool_limit=int(cfg.OIDC_JWKS_POOL_LIMIT),
            oidc_jwks_background_refresh=bool(cfg.OIDC_JWKS_BACKGROUND_REFRESH),
            rate_limit_viewer=cfg.RATE_LIMIT_VIEWER,
            rate_limit_ops=cfg.RATE_LIMIT_OPS,
            rate_limit_admin=cfg.RATE_LIMIT_ADMIN,
            rate_limit_window_seconds=int(cfg.RATE_LIMIT_WINDOW_SECONDS),
            rate_limit_score_per_user=int(cfg.RATE_LIMIT_SCORE_PER_USER),
            rate_limit_roi_by_vendor_per_user=int(cfg.RATE_LIMIT_ROI_BY_VENDOR_PER_USER),
            audit_enabled=bool(cfg.SECURITY_ENABLE_AUDIT),
        )


class ObservabilitySettings(SettingsGroup):
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    sentry_dsn: str | None
    sentry_traces_sample_rate: float
    sentry_profiles_sample_rate: float
    metrics_textfile_dir: str
    metrics_flush_interval_s: float
    prometheus_multiproc_dir: str | None
    enable_metrics: bool
    worker_metrics_http: bool
    worker_metrics_port: int

    @classmethod
    def from_settings(cls, cfg: Settings) -> ObservabilitySettings:
        return cls(
            log_level=cfg.LOG_LEVEL,
            sentry_dsn=cfg.SENTRY_DSN,
            sentry_traces_sample_rate=float(cfg.SENTRY_TRACES_SAMPLE_RATE),
            sentry_profiles_sample_rate=float(cfg.SENTRY_PROFILES_SAMPLE_RATE),
            metrics_textfile_dir=cfg.METRICS_TEXTFILE_DIR,
            metrics_flush_interval_s=float(cfg.METRICS_FLUSH_INTERVAL_S),
            prometheus_multiproc_dir=cfg.PROMETHEUS_MULTIPROC_DIR,
            enable_metrics=bool(cfg.ENABLE_METRICS),
            worker_metrics_http=bool(cfg.WORKER_METRICS_HTTP),
            worker_metrics_port=int(cfg.WORKER_METRICS_PORT),
        )


class LLMSettings(SettingsGroup):
    provider: str
    fallback_provider: str
    local_url: str
    lan_api_base_url: str
    lan_health_base_url: str
    lan_health_timeout_s: float
    lan_api_key: str | None
    remote_url: str | None
    openai_model: str
    openai_api_key: str | None
    openai_api_base: str | None
    request_timeout_s: float

    @classmethod
    def from_settings(cls, cfg: Settings) -> LLMSettings:
        return cls(
            provider=cfg.LLM_PROVIDER,
            fallback_provider=cfg.LLM_PROVIDER_FALLBACK,
            local_url=cfg.LLM_URL,
            lan_api_base_url=cfg.LLM_BASE_URL,
            lan_health_base_url=cfg.LAN_BASE_URL,
            lan_health_timeout_s=float(cfg.LLM_LAN_HEALTH_TIMEOUT_S),
            lan_api_key=cfg.LLM_API_KEY,
            remote_url=cfg.LLM_REMOTE_URL,
            openai_model=cfg.OPENAI_MODEL,
            openai_api_key=cfg.OPENAI_API_KEY,
            openai_api_base=cfg.OPENAI_API_BASE,
            request_timeout_s=float(cfg.LLM_REQUEST_TIMEOUT_S),
        )


class StatsSettings(SettingsGroup):
    enable_cache: bool
    cache_ttl_s: int
    roi_cache_ttl_seconds: float
    namespace: str
    max_days: int
    require_clamp: bool
    use_sql: bool
    returns_view_name: str

    @classmethod
    def from_settings(cls, cfg: Settings) -> StatsSettings:
        return cls(
            enable_cache=bool(cfg.STATS_ENABLE_CACHE),
            cache_ttl_s=int(cfg.STATS_CACHE_TTL_S),
            roi_cache_ttl_seconds=float(cfg.ROI_CACHE_TTL_SECONDS),
            namespace=cfg.STATS_CACHE_NAMESPACE,
            max_days=int(cfg.STATS_MAX_DAYS),
            require_clamp=bool(cfg.REQUIRE_CLAMP),
            use_sql=bool(cfg.STATS_USE_SQL),
            returns_view_name=cfg.RETURNS_STATS_VIEW_NAME,
        )


class RoiSettings(SettingsGroup):
    view_name: str
    materialized_view_name: str

    @classmethod
    def from_settings(cls, cfg: Settings) -> RoiSettings:
        return cls(
            view_name=cfg.ROI_VIEW_NAME,
            materialized_view_name=cfg.ROI_MATERIALIZED_VIEW_NAME,
        )


class AlertSettings(SettingsGroup):
    enabled: bool
    telegram_token: str
    default_chat_id: int | str | None
    api_base: str
    rules_source: Literal["yaml", "db"]
    rules_file: str
    rules_path: str
    rules_watch: bool
    rules_watch_interval_s: float
    rules_override: str | None
    evaluation_cron: str
    schedule_cron: str
    eval_concurrency: int
    send_concurrency: int
    telegram_max_rps: float
    telegram_max_chat_rps: float
    rule_timeout_s: float
    telegram_connect_timeout_s: float
    telegram_total_timeout_s: float

    @classmethod
    def from_settings(cls, cfg: Settings) -> AlertSettings:
        return cls(
            enabled=bool(cfg.ALERTS_ENABLED),
            telegram_token=cfg.TELEGRAM_TOKEN,
            default_chat_id=cfg.TELEGRAM_DEFAULT_CHAT_ID,
            api_base=cfg.TELEGRAM_API_BASE,
            rules_source=cfg.ALERT_RULES_SOURCE,
            rules_file=cfg.ALERT_RULES_FILE,
            rules_path=cfg.ALERT_RULES_PATH,
            rules_watch=bool(cfg.ALERT_RULES_WATCH),
            rules_watch_interval_s=float(cfg.ALERT_RULES_WATCH_INTERVAL_S),
            rules_override=cfg.ALERT_RULES_OVERRIDE,
            evaluation_cron=cfg.ALERTS_EVALUATION_INTERVAL_CRON,
            schedule_cron=cfg.ALERT_SCHEDULE_CRON,
            eval_concurrency=int(cfg.ALERT_EVAL_CONCURRENCY),
            send_concurrency=int(cfg.ALERT_SEND_CONCURRENCY),
            telegram_max_rps=float(cfg.ALERT_TELEGRAM_MAX_RPS),
            telegram_max_chat_rps=float(cfg.ALERT_TELEGRAM_MAX_CHAT_RPS),
            rule_timeout_s=float(cfg.ALERT_RULE_TIMEOUT_S),
            telegram_connect_timeout_s=float(cfg.TELEGRAM_CONNECT_TIMEOUT_S),
            telegram_total_timeout_s=float(cfg.TELEGRAM_TOTAL_TIMEOUT_S),
        )


class EtlSettings(SettingsGroup):
    connect_timeout_s: float
    read_timeout_s: float
    total_timeout_s: float
    pool_timeout_s: float
    http_keepalive: int
    http_max_connections: int
    retry_attempts: int
    retry_base_s: float
    retry_max_s: float
    retry_jitter_s: float
    retry_status_codes: Iterable[int]
    use_copy: bool
    ingest_chunk_size_mb: int
    ingest_streaming_chunk_size: int
    ingest_streaming_enabled: bool
    ingest_idempotent: bool
    analyze_min_rows: int
    enable_live: bool
    task_id: str | None
    helium_api_key: str | None
    helium10_key: str | None
    keepa_key: str | None
    region: str
    sp_fees_date: str | None
    sp_refresh_token: str | None
    sp_client_id: str | None
    sp_client_secret: str | None
    sp_api_base_url: str | None

    @classmethod
    def from_settings(cls, cfg: Settings) -> EtlSettings:
        return cls(
            connect_timeout_s=float(cfg.ETL_CONNECT_TIMEOUT_S),
            read_timeout_s=float(cfg.ETL_READ_TIMEOUT_S),
            total_timeout_s=float(cfg.ETL_TOTAL_TIMEOUT_S),
            pool_timeout_s=float(cfg.ETL_POOL_TIMEOUT_S),
            http_keepalive=int(cfg.ETL_HTTP_KEEPALIVE),
            http_max_connections=int(cfg.ETL_HTTP_MAX_CONNECTIONS),
            retry_attempts=int(cfg.ETL_RETRY_ATTEMPTS),
            retry_base_s=float(cfg.ETL_RETRY_BASE_S),
            retry_max_s=float(cfg.ETL_RETRY_MAX_S),
            retry_jitter_s=float(cfg.ETL_RETRY_JITTER_S),
            retry_status_codes=list(cfg.ETL_RETRY_STATUS_CODES or []),
            use_copy=bool(cfg.USE_COPY),
            ingest_chunk_size_mb=int(cfg.INGEST_CHUNK_SIZE_MB),
            ingest_streaming_chunk_size=int(cfg.INGEST_STREAMING_CHUNK_SIZE),
            ingest_streaming_enabled=bool(cfg.INGEST_STREAMING_ENABLED),
            ingest_idempotent=bool(cfg.INGEST_IDEMPOTENT),
            analyze_min_rows=int(cfg.ANALYZE_MIN_ROWS),
            enable_live=bool(cfg.ENABLE_LIVE),
            task_id=cfg.TASK_ID,
            helium_api_key=cfg.HELIUM_API_KEY,
            helium10_key=cfg.HELIUM10_KEY,
            keepa_key=cfg.KEEPA_KEY,
            region=cfg.REGION,
            sp_fees_date=cfg.SP_FEES_DATE,
            sp_refresh_token=cfg.SP_REFRESH_TOKEN,
            sp_client_id=cfg.SP_CLIENT_ID,
            sp_client_secret=cfg.SP_CLIENT_SECRET,
            sp_api_base_url=cfg.SP_API_BASE_URL,
        )


class MaintenanceSettings(SettingsGroup):
    table_list: list[str]
    vacuum_enabled: bool

    @classmethod
    def from_settings(cls, cfg: Settings) -> MaintenanceSettings:
        return cls(
            table_list=_split_csv(cfg.TABLE_MAINTENANCE_LIST),
            vacuum_enabled=bool(cfg.VACUUM_ENABLE),
        )


class EmailSettings(SettingsGroup):
    host: str
    username: str
    password: str

    @classmethod
    def from_settings(cls, cfg: Settings) -> EmailSettings:
        return cls(
            host=cfg.IMAP_HOST,
            username=cfg.IMAP_USER,
            password=cfg.IMAP_PASS,
        )


class RepricerSettings(SettingsGroup):
    min_roi: Decimal
    buybox_gap: Decimal
    rounding_quant: Decimal

    @classmethod
    def from_settings(cls, cfg: Settings) -> RepricerSettings:
        return cls(
            min_roi=Decimal(str(cfg.REPRICER_MIN_ROI)),
            buybox_gap=Decimal(str(cfg.REPRICER_BUYBOX_GAP)),
            rounding_quant=Decimal(str(cfg.REPRICER_ROUND)),
        )


__all__ = [
    "AlertSettings",
    "AppSettings",
    "CelerySettings",
    "DatabaseSettings",
    "EmailSettings",
    "EtlSettings",
    "LLMSettings",
    "MaintenanceSettings",
    "ObservabilitySettings",
    "RoiSettings",
    "RedisSettings",
    "RepricerSettings",
    "S3Settings",
    "SecuritySettings",
    "SettingsGroup",
    "StatsSettings",
]
