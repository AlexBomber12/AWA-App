import os
import requests  # type: ignore
from pg_utils import connect


def main():
    live = os.getenv("ENABLE_LIVE") == "1"
    dsn = os.environ["DATABASE_URL"]
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
