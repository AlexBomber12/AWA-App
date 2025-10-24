from __future__ import annotations

import os

from awa_common.dsn import build_dsn

from pg_utils import connect
from sp_api.api import SellingPartnerAPI


def main() -> None:
    live = os.getenv("ENABLE_LIVE") == "1"
    dsn = build_dsn()
    conn = connect(dsn)
    cur = conn.cursor()
    skus = ["SKU1", "SKU2"]
    if live:
        api = SellingPartnerAPI()
        for sku in skus:
            data = api.get_my_fees_estimate_for_sku(seller_sku=sku)
            cur.execute("INSERT INTO fees_raw VALUES (%s, %s)", (sku, data))
    else:
        for sku in skus:
            cur.execute("INSERT INTO fees_raw VALUES (%s, %s)", (sku, "{}"))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
