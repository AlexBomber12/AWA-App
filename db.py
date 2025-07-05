import os
from pathlib import Path


def pg_dsn() -> str:
    if "PG_DSN" in os.environ:
        return os.environ["PG_DSN"]
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    if os.getenv("PG_USER"):
        return (
            f"postgresql+asyncpg://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
            f"@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT', 5432)}/{os.getenv('PG_DATABASE')}"
        )
    data_dir = os.getenv("DATA_DIR", str(Path.cwd() / "data"))
    return f"sqlite+aiosqlite:///{data_dir}/awa.db"
