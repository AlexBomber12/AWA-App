import os
import json
import sqlite3
import psycopg2
from db import pg_dsn


def main() -> int:
    live = os.getenv("ENABLE_LIVE") == "1"
    refresh_token = os.environ["SP_REFRESH_TOKEN"]
    client_id = os.environ["SP_CLIENT_ID"]
    client_secret = os.environ["SP_CLIENT_SECRET"]
    region = os.environ["REGION"]
    dsn = pg_dsn()
    skus = ["DUMMY1", "DUMMY2"]
    if live:
        from sp_api.api import SellingPartnerAPI

        api = SellingPartnerAPI(  # type: ignore[call-arg]
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            region=region,
        )
        results = []
        for sku in skus:
            r = api.get_my_fees_estimate_for_sku(sku)
            amt = r["payload"]["FeesEstimateResult"]["FeesEstimate"][
                "TotalFeesEstimate"
            ]["Amount"]
            results.append((sku, amt))
    else:
        with open("tests/fixtures/spapi_fees_sample.json") as f:
            data = json.load(f)
        results = [
            (
                r["sku"],
                r["payload"]["FeesEstimateResult"]["FeesEstimate"]["TotalFeesEstimate"][
                    "Amount"
                ],
            )
            for r in data
        ]
    if dsn.startswith("sqlite"):
        conn = sqlite3.connect(dsn.replace("sqlite:///", ""))
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS fees_raw("
            "sku text primary key, fee numeric, captured_at timestamptz default current_timestamp)"
        )
        for sku, fee in results:
            cur.execute(
                "INSERT INTO fees_raw(sku, fee) VALUES (?, ?) "
                "ON CONFLICT(sku) DO UPDATE SET fee = excluded.fee",
                (sku, fee),
            )
    else:
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
