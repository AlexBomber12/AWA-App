import os


def pg_dsn() -> str:
    if "PG_DSN" in os.environ:
        return os.environ["PG_DSN"]
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    return "sqlite:///data/awa.db"
