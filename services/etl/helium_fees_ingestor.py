import json
import os
import urllib.request

from pg_utils import connect


ASINS = ["DUMMY1", "DUMMY2"]


def main() -> int:
    live = os.getenv("ENABLE_LIVE") == "1"
    api_key = os.environ["HELIUM_API_KEY"]
    dsn = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:pass@postgres:5432/postgres",  # pragma: allowlist secret
    )
    if live:
        results = []
        for asin in ASINS:
            url = f"https://api.helium10.com/v1/profits/fees?asin={asin}"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
            with urllib.request.urlopen(req) as resp:
                data = json.load(resp)
            results.append((asin, data["totalFbaFee"]))
    else:
        with open("tests/fixtures/helium_fees_sample.json") as f:
            data = json.load(f)
        results = [(r["sku"], r["totalFbaFee"]) for r in data]
    conn = connect(dsn.replace("postgresql+asyncpg://", "postgresql://"))
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
