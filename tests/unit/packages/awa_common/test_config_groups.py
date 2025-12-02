from awa_common.settings import Settings


def test_database_and_redis_settings(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@db/app")
    monkeypatch.setenv("PG_ASYNC_DSN", "postgresql+asyncpg://user:pass@db/app")
    monkeypatch.setenv("REDIS_URL", "redis://cache:6379/0")
    monkeypatch.setenv("BROKER_URL", "redis://broker:6379/1")
    monkeypatch.setenv("QUEUE_NAMES", "ingest,alerts")
    monkeypatch.setenv("CACHE_REDIS_URL", "redis://cache:6379/2")
    monkeypatch.setenv("CACHE_DEFAULT_TTL_S", "900")
    monkeypatch.setenv("CACHE_NAMESPACE", "stats:")
    monkeypatch.setenv("REDIS_BACKLOG_WARN_SIZE", "42")
    monkeypatch.setenv("REDIS_BACKLOG_WARN_INTERVAL_S", "5")
    cfg = Settings()
    assert cfg.db.url.endswith("/app")
    assert cfg.db.async_dsn.startswith("postgresql+asyncpg://")
    assert cfg.redis.url == "redis://cache:6379/0"
    assert cfg.redis.broker_url == "redis://broker:6379/1"
    assert cfg.redis.queue_names == ["ingest", "alerts"]
    assert cfg.redis.cache_url == "redis://cache:6379/2"
    assert cfg.redis.cache_ttl_s == 900
    assert cfg.redis.cache_namespace == "stats:"
    assert cfg.redis.backlog_warn_size == 42
    assert cfg.redis.backlog_warn_interval_s == 5.0


def test_s3_and_celery_settings(monkeypatch):
    monkeypatch.setenv("MINIO_ENDPOINT", "minio.example:9000")
    monkeypatch.setenv("MINIO_SECURE", "1")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "key")
    monkeypatch.setenv("MINIO_SECRET_KEY", "secret")
    monkeypatch.setenv("MINIO_BUCKET", "bucket-name")
    monkeypatch.setenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "3")
    monkeypatch.setenv("CELERY_TASK_TIME_LIMIT", "120")
    monkeypatch.setenv("CELERY_TASK_STORE_EAGER_RESULT", "1")
    monkeypatch.setenv("CELERY_RESULT_EXPIRES", "600")
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "1")
    monkeypatch.setenv("CELERY_LOOP_LAG_MONITOR", "0")
    monkeypatch.setenv("CELERY_LOOP_LAG_INTERVAL_S", "2.5")
    monkeypatch.setenv("BACKLOG_PROBE_SECONDS", "9")
    monkeypatch.setenv("SCHEDULE_LOGISTICS_ETL", "1")
    monkeypatch.setenv("LOGISTICS_CRON", "0 5 * * *")
    cfg = Settings()
    s3_cfg = cfg.s3
    celery_cfg = cfg.celery
    assert s3_cfg.endpoint == "minio.example:9000"
    assert s3_cfg.secure is True
    assert s3_cfg.bucket == "bucket-name"
    assert celery_cfg.prefetch_multiplier == 3
    assert celery_cfg.task_time_limit == 120
    assert celery_cfg.store_eager_result is True
    assert celery_cfg.result_expires == 600
    assert celery_cfg.always_eager is True
    assert celery_cfg.loop_lag_monitor_enabled is False
    assert celery_cfg.backlog_probe_seconds == 9
    assert celery_cfg.schedule_logistics_etl is True
    assert celery_cfg.logistics_cron == "0 5 * * *"


def test_celery_settings_alertbot_cron(monkeypatch):
    monkeypatch.setenv("CHECK_INTERVAL_MIN", "7")
    monkeypatch.setenv("ALERTS_EVALUATION_INTERVAL_CRON", "*/3 * * * *")
    cfg = Settings()
    assert cfg.celery.alertbot_cron == "*/7 * * * *"

    monkeypatch.delenv("CHECK_INTERVAL_MIN", raising=False)
    cfg_no_override = Settings()
    assert cfg_no_override.celery.alertbot_cron == cfg_no_override.ALERTS_EVALUATION_INTERVAL_CRON


def test_llm_and_observability_settings(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "cloud")
    monkeypatch.setenv("LLM_SECONDARY_PROVIDER", "local")
    monkeypatch.setenv("LLM_BASE_URL", "http://gateway:9000")
    monkeypatch.setenv("LLM_PROVIDER_BASE_URL", "http://local-llm:8001")
    monkeypatch.setenv("LLM_API_KEY", "lan-key")
    monkeypatch.setenv("LLM_LOCAL_MODEL", "local-m")
    monkeypatch.setenv("LLM_CLOUD_MODEL", "gpt-5-turbo")
    monkeypatch.setenv("LLM_CLOUD_API_KEY", "openai-key")
    monkeypatch.setenv("LLM_REQUEST_TIMEOUT_SEC", "42")
    monkeypatch.setenv("LLM_MAX_RETRIES", "7")
    monkeypatch.setenv("LLM_BACKOFF_BASE_MS", "250")
    monkeypatch.setenv("LLM_BACKOFF_MAX_MS", "2000")
    monkeypatch.setenv("LLM_BIN_TIMEOUT_SEC", "12")
    monkeypatch.setenv("LLM_MAX_OUTPUT_BYTES", "2048")
    monkeypatch.setenv("LLM_EMAIL_CLOUD_THRESHOLD_CHARS", "5")
    monkeypatch.setenv("LLM_PRICELIST_CLOUD_THRESHOLD_ROWS", "10")
    monkeypatch.setenv("LLM_MIN_CONFIDENCE", "0.25")
    monkeypatch.setenv("LLM_LAN_HEALTH_TIMEOUT_S", "2")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "0.2")
    monkeypatch.setenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")
    cfg = Settings()
    llm_cfg = cfg.llm
    observability = cfg.observability
    assert llm_cfg.provider == "cloud"
    assert llm_cfg.secondary_provider == "local"
    assert llm_cfg.base_url == "http://gateway:9000"
    assert llm_cfg.provider_base_url == "http://local-llm:8001"
    assert llm_cfg.api_key == "lan-key"
    assert llm_cfg.local_model == "local-m"
    assert llm_cfg.cloud_model == "gpt-5-turbo"
    assert llm_cfg.cloud_api_key == "openai-key"
    assert llm_cfg.email_cloud_threshold_chars == 5
    assert llm_cfg.pricelist_cloud_threshold_rows == 10
    assert llm_cfg.min_confidence == 0.25
    assert llm_cfg.request_timeout_s == 42.0
    assert llm_cfg.max_retries == 7
    assert llm_cfg.backoff_base_ms == 250.0
    assert llm_cfg.backoff_max_ms == 2000.0
    assert llm_cfg.bin_timeout_s == 12.0
    assert llm_cfg.max_output_bytes == 2048
    assert observability.sentry_traces_sample_rate == 0.2
    assert observability.sentry_profiles_sample_rate == 0.1


def test_roi_settings(monkeypatch):
    monkeypatch.setenv("ROI_VIEW_NAME", "custom_view")
    monkeypatch.setenv("ROI_MATERIALIZED_VIEW_NAME", "custom_mat")
    cfg = Settings()
    assert cfg.roi.view_name == "custom_view"
    assert cfg.roi.materialized_view_name == "custom_mat"


def test_limiter_settings(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_VIEWER", "10/minute")
    monkeypatch.setenv("RATE_LIMIT_OPS", "20/minute")
    monkeypatch.setenv("RATE_LIMIT_ADMIN", "30/minute")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "120")
    monkeypatch.setenv("RATE_LIMIT_SCORE_PER_USER", "3")
    monkeypatch.setenv("RATE_LIMIT_ROI_BY_VENDOR_PER_USER", "4")
    monkeypatch.setenv("LIMITER_NEAR_LIMIT_THRESHOLD", "0.8")
    monkeypatch.setenv("LIMITER_WARN_INTERVAL_S", "5")
    cfg = Settings()
    limiter = cfg.limiter
    assert limiter.viewer_limit == "10/minute"
    assert limiter.ops_limit == "20/minute"
    assert limiter.admin_limit == "30/minute"
    assert limiter.window_seconds == 120
    assert limiter.score_per_user == 3
    assert limiter.roi_by_vendor_per_user == 4
    assert limiter.near_limit_threshold == 0.8
    assert limiter.warn_interval_s == 5.0


def test_ingestion_settings(monkeypatch):
    monkeypatch.setenv("MAX_REQUEST_BYTES", "1024")
    monkeypatch.setenv("INGEST_CHUNK_SIZE_MB", "2")
    monkeypatch.setenv("INGEST_STREAMING_ENABLED", "0")
    monkeypatch.setenv("INGEST_STREAMING_THRESHOLD_MB", "10")
    monkeypatch.setenv("INGEST_STREAMING_CHUNK_SIZE_MB", "4")
    monkeypatch.setenv("INGEST_STREAMING_CHUNK_SIZE", "123")
    monkeypatch.setenv("SPOOL_MAX_BYTES", "500")
    monkeypatch.setenv("INGEST_IDEMPOTENT", "0")
    monkeypatch.setenv("ANALYZE_MIN_ROWS", "999")
    monkeypatch.setenv("QUEUE_NAMES", "ingest,alerts")
    cfg = Settings()
    ingest = cfg.ingestion
    assert ingest.max_request_bytes == 1024
    assert ingest.chunk_size_mb == 2
    assert ingest.streaming_enabled is False
    assert ingest.streaming_threshold_mb == 10
    assert ingest.streaming_chunk_size_mb == 4
    assert ingest.streaming_chunk_size == 123
    assert ingest.spool_max_bytes == 500
    assert ingest.ingest_idempotent is False
    assert ingest.analyze_min_rows == 999
    assert ingest.queue_names == ["ingest", "alerts"]
