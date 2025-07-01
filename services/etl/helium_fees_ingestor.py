import os, json, urllib.request
import psycopg2


def main() -> int:
    live = os.getenv("ENABLE_LIVE") == "1"
    api_key = os.environ.get("HELIUM_API_KEY")
    dsn = os.environ.get("PG_DSN")
    asins = ["DUMMY1", "DUMMY2"]
    results = []
    if live:
        for asin in asins:
            req = urllib.request.Request(
                f"https://api.helium10.com/v1/profits/fees?asin={asin}",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            with urllib.request.urlopen(req) as r:
                data = json.load(r)
            results.append((asin, data.get("totalFbaFee")))
    else:
        with open("tests/fixtures/helium_fees_sample.json") as f:
            data = json.load(f)
        results = [(r["sku"], r.get("totalFbaFee")) for r in data]
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
