from awa_common.settings import settings

db_cfg = getattr(settings, "db", None)
DATABASE_URL = (
    db_cfg.url if db_cfg else getattr(settings, "DATABASE_URL", "postgresql+asyncpg://postgres:pass@localhost:5432/awa")
)
