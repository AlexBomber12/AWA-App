import os
import requests
import sqlite3
import psycopg2
from db import pg_dsn


def main():
    live = os.getenv("ENABLE_LIVE") == "1"
    dsn = pg_dsn()
    if dsn.startswith("sqlite"):
        conn = sqlite3.connect(dsn.replace("sqlite:///", ""))
        cur = conn.cursor()
    else:
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
    skus = ["DUMMY1", "DUMMY2"]
    if live:
        for sku in skus:
            r = requests.get(f"https://api.example.com/{sku}")
            if dsn.startswith("sqlite"):
                cur.execute("INSERT INTO fees_raw VALUES (?, ?)", (sku, r.json()))
            else:
                cur.execute("INSERT INTO fees_raw VALUES (%s, %s)", (sku, r.json()))
    else:
        for sku in skus:
            if dsn.startswith("sqlite"):
                cur.execute("INSERT INTO fees_raw VALUES (?, ?)", (sku, "{}"))
            else:
                cur.execute("INSERT INTO fees_raw VALUES (%s, %s)", (sku, "{}"))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
