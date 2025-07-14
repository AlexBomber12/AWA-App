import datetime
import io
import json
import os
import sys
import time

import keepa
from minio import Minio
from pg_utils import connect


key = os.environ["KEEPA_KEY"]
minio_endpoint = os.environ["MINIO_ENDPOINT"]
minio_access = os.environ["MINIO_ACCESS_KEY"]
minio_secret = os.environ["MINIO_SECRET_KEY"]
dsn = os.environ["DATABASE_URL"]

start = time.time()
if os.getenv("ENABLE_LIVE") == "1":
    api = keepa.Keepa(key)
    params = {
        "current_SALES_lte": 80000,
        "current_BUY_BOX_SHIPPING_gte": 2000,
        "current_COUNT_NEW_lte": 10,
    }
    data = json.dumps(api.product_finder(params, domain="IT", n_products=20000)).encode()
else:
    with open("fixtures/keepa_sample.json") as f:
        data = json.dumps(json.load(f)).encode()
duration = time.time() - start
date = datetime.date.today()
path = f"raw/{date:%Y/%m/%d}/asins.json"
bucket = "keepa"
mc = Minio(minio_endpoint, access_key=minio_access, secret_key=minio_secret, secure=False)
if not mc.bucket_exists(bucket):
    mc.make_bucket(bucket)
mc.put_object(bucket, path, io.BytesIO(data), len(data))
conn = connect(dsn)
cur = conn.cursor()
cur.execute(
    "INSERT INTO etl_log(date,asin_count,duration_sec) VALUES (%s,%s,%s)",
    (date, len(json.loads(data)), duration),
)
conn.commit()
cur.close()
conn.close()
sys.exit(0)
