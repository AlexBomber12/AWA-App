import os


def make_dsn() -> str:
    return (
        f"postgresql+asyncpg://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT', 5432)}/{os.getenv('PG_DATABASE')}"
    )


def build_url(async_: bool = False) -> str:
    if os.getenv("ENABLE_LIVE", "1") == "0":
        return (
            f"sqlite+aiosqlite:///{os.getenv('DATA_DIR', str(os.getcwd() + '/data'))}/awa.db"
            if async_
            else f"sqlite:///{os.getenv('DATA_DIR', str(os.getcwd() + '/data'))}/awa.db"
        )

    url = make_dsn()
    if not async_:
        url = url.replace("asyncpg", "psycopg")
    return url
