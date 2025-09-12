import json
import logging
import os
from typing import Any, List, Mapping

import httpx
from sqlalchemy import create_engine

from packages.awa_common.dsn import build_dsn
from services.fees_h10 import repository as repo


def main() -> int:
    live = os.getenv("ENABLE_LIVE") == "1"
    refresh_token = os.getenv("SP_REFRESH_TOKEN", "")
    client_id = os.getenv("SP_CLIENT_ID", "")
    client_secret = os.getenv("SP_CLIENT_SECRET", "")
    region = os.getenv("REGION", "")
    dsn = build_dsn()
    skus = ["DUMMY1", "DUMMY2"]
    rows: List[Mapping[str, Any]] = []
    try:
        if live:
            from typing import cast

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
            for asin in skus:
                r = api.get_my_fees_estimate_for_sku(asin)
                amt = r["payload"]["FeesEstimateResult"]["FeesEstimate"][
                    "TotalFeesEstimate"
                ]["Amount"]
                rows.append(
                    {
                        "asin": asin,
                        "marketplace": region or "US",
                        "fee_type": "fba_pick_pack",
                        "amount": amt,
                        "currency": "USD",
                        "source": "sp",
                        "effective_date": os.getenv("SP_FEES_DATE"),
                    }
                )
        else:
            with open("tests/fixtures/spapi_fees_sample.json") as f:
                data = json.load(f)
            for r in data:
                rows.append(
                    {
                        "asin": r["asin"],
                        "marketplace": "US",
                        "fee_type": "fba_pick_pack",
                        "amount": r["payload"]["FeesEstimateResult"]["FeesEstimate"][
                            "TotalFeesEstimate"
                        ]["Amount"],
                        "currency": "USD",
                        "source": "sp",
                        "effective_date": r.get("date"),
                    }
                )
    except (
        httpx.TimeoutException,
        httpx.RequestError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        logging.error("sp fees fetch failed: %s", exc)
        return 1
    engine = create_engine(dsn)
    repo.upsert_fees_raw(engine, rows, testing=os.getenv("TESTING") == "1")
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
