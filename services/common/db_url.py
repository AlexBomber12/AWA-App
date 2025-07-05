import os


def build_url(async_: bool = False) -> str:
    if os.getenv("ENABLE_LIVE", "1") == "0":
        return (
            f"sqlite+aiosqlite:///{os.getenv('DATA_DIR', str(os.getcwd() + '/data'))}/awa.db"
            if async_
            else f"sqlite:///{os.getenv('DATA_DIR', str(os.getcwd() + '/data'))}/awa.db"
        )

    scheme = "postgresql+asyncpg" if async_ else "postgresql+psycopg"
    user = os.getenv("PG_USER", "postgres")
    pwd = os.getenv("PG_PASSWORD", "pass")
    host = os.getenv("PG_HOST", "postgres")
    db = os.getenv("PG_DATABASE", "awa")
    return f"{scheme}://{user}:{pwd}@{host}:5432/{db}"
