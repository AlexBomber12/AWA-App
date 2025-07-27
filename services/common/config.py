import os

raw = os.getenv("DATABASE_URL", "postgresql://postgres:pass@localhost:5432/awa")
if raw.startswith("postgres://"):
    raw = raw.replace("postgres://", "postgresql://", 1)

ASYNC_DSN = raw.replace("postgresql://", "postgresql+asyncpg://", 1)
SYNC_DSN = raw
