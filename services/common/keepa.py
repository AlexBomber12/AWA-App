from sqlalchemy import create_engine, text
from .dsn import build_dsn


def list_active_asins() -> list[str]:
    engine = create_engine(build_dsn(sync=True))
    with engine.begin() as conn:
        res = conn.execute(text("SELECT asin FROM products"))
        return [r[0] for r in res.fetchall()]
