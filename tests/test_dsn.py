import os
from services.common.dsn import build_dsn


def test_build_dsn_sync_suffix():
    os.environ.pop("DATABASE_URL", None)
    dsn = build_dsn(sync=True)
    assert "+psycopg" in dsn
