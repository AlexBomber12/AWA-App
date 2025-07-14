import os


def pg_dsn() -> str:
    """Return DATABASE_URL from the environment."""
    return os.environ["DATABASE_URL"]
