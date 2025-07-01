import os
import requests
import psycopg2


def main() -> int:
    live = os.getenv("ENABLE_LIVE") == "1"
    dsn = os.environ["PG_DSN"]
    skus = ["DUMMY1", "DUMMY2"]
    if live:
        results = []
        for sku in skus:
            r = requests.get(f"https://example.com/{sku}")
            r.raise_for_status()
            data = r.json()
            results.append((sku, data["fee"]))
    else:
        results = [("DUMMY1", 1.11), ("DUMMY2", 2.22)]
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS fees_raw("
        "sku text primary key, fee numeric, captured_at timestamptz default now())"
    )
    for sku, fee in results:
        cur.execute(
            "INSERT INTO fees_raw(sku, fee) VALUES (%s, %s) "
            "ON CONFLICT (sku) DO UPDATE SET fee = EXCLUDED.fee",
            (sku, fee),
        )
    conn.commit()
    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
