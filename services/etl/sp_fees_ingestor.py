import json
import os

from pg_utils import connect
from services.common.dsn import build_dsn


def main() -> int:
    live = os.getenv("ENABLE_LIVE") == "1"
    refresh_token = os.getenv("SP_REFRESH_TOKEN", "")
    client_id = os.getenv("SP_CLIENT_ID", "")
    client_secret = os.getenv("SP_CLIENT_SECRET", "")
    region = os.getenv("REGION", "")
    dsn = build_dsn()
    skus = ["DUMMY1", "DUMMY2"]
    if live:
        from typing import Any, cast

        from sp_api.api import SellingPartnerAPI

        api = cast(
            Any,
            cast(Any, SellingPartnerAPI)(
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                region=region,
            ),
        )
        results = []
        for asin in skus:
            r = api.get_my_fees_estimate_for_sku(asin)
            amt = r["payload"]["FeesEstimateResult"]["FeesEstimate"][
                "TotalFeesEstimate"
            ]["Amount"]
            results.append((asin, amt))
    else:
        with open("tests/fixtures/spapi_fees_sample.json") as f:
            data = json.load(f)
        results = [
            (
                r["asin"],
                r["payload"]["FeesEstimateResult"]["FeesEstimate"]["TotalFeesEstimate"][
                    "Amount"
                ],
            )
            for r in data
        ]
    conn = connect(dsn)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS fees_raw(asin text primary key, fee numeric, captured_at timestamptz default now())"
    )
    for asin, fee in results:
        cur.execute(
            "INSERT INTO fees_raw(asin, fee) VALUES (%s, %s) ON CONFLICT (asin) DO UPDATE SET fee = EXCLUDED.fee",
            (asin, fee),
        )
    conn.commit()
    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
