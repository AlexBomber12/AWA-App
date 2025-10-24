from __future__ import annotations

import os

import requests
from awa_common.dsn import build_dsn

from pg_utils import connect


def main() -> None:
    live = os.getenv("ENABLE_LIVE") == "1"
    dsn = build_dsn()
    conn = connect(dsn)
    cur = conn.cursor()
    skus = ["DUMMY1", "DUMMY2"]
    if live:
        for sku in skus:
            r = requests.get(f"https://api.example.com/{sku}")
            cur.execute("INSERT INTO fees_raw VALUES (%s, %s)", (sku, r.json()))
    else:
        for sku in skus:
            cur.execute("INSERT INTO fees_raw VALUES (%s, %s)", (sku, "{}"))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
