import os
import requests
import psycopg2


def main():
    live = os.getenv("ENABLE_LIVE") == "1"
    dsn = os.environ["PG_DSN"]
    conn = psycopg2.connect(dsn)
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
