import os


def pg_dsn() -> str:
    if "PG_DSN" in os.environ:
        return os.environ["PG_DSN"]
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    user = os.getenv("POSTGRES_USER", "appuser")
    password = os.getenv("POSTGRES_PASSWORD", "apppass")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "appdb")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"
