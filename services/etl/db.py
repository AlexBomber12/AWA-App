import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:pass@localhost:5432/awa")
