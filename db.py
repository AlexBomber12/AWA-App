import os


def pg_dsn() -> str:
    if "PG_DSN" in os.environ:
        return os.environ["PG_DSN"]
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    return (
        f"postgresql+asyncpg://{os.getenv('PG_USER', 'postgres')}:{os.getenv('PG_PASSWORD', 'pass')}"
        f"@{os.getenv('PG_HOST', 'postgres')}:{os.getenv('PG_PORT', 5432)}/{os.getenv('PG_DATABASE', 'awa')}"
    )
