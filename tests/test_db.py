from db import pg_dsn


def test_pg_dsn_contains_postgres() -> None:
    assert "postgresql" in pg_dsn()
