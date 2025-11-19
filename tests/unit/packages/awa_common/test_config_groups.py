from awa_common.settings import Settings


def test_database_and_redis_settings(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@db/app")
    monkeypatch.setenv("PG_ASYNC_DSN", "postgresql+asyncpg://user:pass@db/app")
    monkeypatch.setenv("REDIS_URL", "redis://cache:6379/0")
    monkeypatch.setenv("BROKER_URL", "redis://broker:6379/1")
    monkeypatch.setenv("QUEUE_NAMES", "ingest,alerts")
    cfg = Settings()
    assert cfg.db.url.endswith("/app")
    assert cfg.db.async_dsn.startswith("postgresql+asyncpg://")
    assert cfg.redis.url == "redis://cache:6379/0"
    assert cfg.redis.broker_url == "redis://broker:6379/1"
    assert cfg.redis.queue_names == ["ingest", "alerts"]


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


def test_llm_and_observability_settings(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_PROVIDER_FALLBACK", "stub")
    monkeypatch.setenv("LLM_URL", "http://llm:9000/llm")
    monkeypatch.setenv("LLM_BASE_URL", "http://lan:9000")
    monkeypatch.setenv("LLM_API_KEY", "lan-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("LLM_LAN_HEALTH_TIMEOUT_S", "2")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "0.2")
    monkeypatch.setenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")
    cfg = Settings()
    llm_cfg = cfg.llm
    observability = cfg.observability
    assert llm_cfg.provider == "openai"
    assert llm_cfg.fallback_provider == "stub"
    assert llm_cfg.local_url.endswith(":9000/llm")
    assert llm_cfg.lan_api_key == "lan-key"
    assert llm_cfg.openai_model == "gpt-4o"
    assert llm_cfg.openai_api_key == "openai-key"
    assert llm_cfg.lan_health_timeout_s == 2.0
    assert observability.sentry_traces_sample_rate == 0.2
    assert observability.sentry_profiles_sample_rate == 0.1


def test_roi_settings(monkeypatch):
    monkeypatch.setenv("ROI_VIEW_NAME", "custom_view")
    monkeypatch.setenv("ROI_MATERIALIZED_VIEW_NAME", "custom_mat")
    cfg = Settings()
    assert cfg.roi.view_name == "custom_view"
    assert cfg.roi.materialized_view_name == "custom_mat"
