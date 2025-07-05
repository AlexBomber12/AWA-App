from sqlalchemy import create_engine, text
from .db_url import build_url


def list_active_asins() -> list[str]:
    engine = create_engine(build_url(async_=False).replace("asyncpg", "psycopg"))
    with engine.begin() as conn:
        res = conn.execute(text("SELECT asin FROM products"))
        return [r[0] for r in res.fetchall()]
