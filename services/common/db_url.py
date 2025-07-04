import os


def build_db_url() -> str:
    if os.getenv("ENABLE_LIVE", "1") == "0":
        return "sqlite+aiosqlite:///data/awa.db"

    pg_user = os.getenv("PG_USER", "postgres")
    pg_pass = os.getenv("PG_PASSWORD", "pass")
    pg_host = os.getenv("PG_HOST", "localhost")
    pg_db = os.getenv("PG_DATABASE", "awa")
    return f"postgresql+asyncpg://{pg_user}:{pg_pass}@{pg_host}:5432/{pg_db}"
