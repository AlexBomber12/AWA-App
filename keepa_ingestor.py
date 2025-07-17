from __future__ import annotations

import datetime
import io
import json
import os
import time
from pathlib import Path

import keepa
from minio import Minio

from pg_utils import connect
from services.common.dsn import build_dsn


def main() -> None:
    live = os.getenv("ENABLE_LIVE") == "1"
    key = os.environ.get("KEEPA_KEY")
    endpoint = os.environ.get("MINIO_ENDPOINT")
    access = os.environ.get("MINIO_ACCESS_KEY")
    secret = os.environ.get("MINIO_SECRET_KEY")
    dsn = build_dsn()
    start = time.time()
    if live:
        api = keepa.Keepa(key)
        params = {
            "sales_rank_lte": 80000,
            "buybox_price_gte": 2000,
            "num_offers_lte": 10,
        }
        asins = api.product_finder(params, domain="IT", n_products=20000)
    else:
        with open("tests/fixtures/keepa_sample.json") as f:
            asins = json.load(f)
    duration = time.time() - start
    today = datetime.date.today()
    if live:
        path = f"raw/{today:%Y/%m/%d}/asins.json"
        mc = Minio(endpoint, access_key=access, secret_key=secret, secure=False)
        if not mc.bucket_exists("keepa"):
            mc.make_bucket("keepa")
        data = json.dumps(asins).encode()
        mc.put_object("keepa", path, io.BytesIO(data), len(data), content_type="application/json")
        conn = connect(dsn)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS etl_log(date date, asin_count int, duration_sec real)"
        )
        cur.execute(
            "INSERT INTO etl_log(date, asin_count, duration_sec) VALUES (%s,%s,%s)",
            (today, len(asins), duration),
        )
        cur.close()
        conn.close()
    else:
        p = Path("tmp/offline_asins.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asins))


if __name__ == "__main__":
    main()
