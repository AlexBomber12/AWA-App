import os, sys, json, datetime, time, io
import keepa
from minio import Minio
import psycopg2

key=os.environ['KEEPA_KEY']
minio_endpoint=os.environ['MINIO_ENDPOINT']
minio_access=os.environ['MINIO_ACCESS_KEY']
minio_secret=os.environ['MINIO_SECRET_KEY']
pg_dsn=os.environ['PG_DSN']

api=keepa.Keepa(key)
start=time.time()
params={
    "current_SALES_lte":80000,
    "current_BUY_BOX_SHIPPING_gte":2000,
    "current_COUNT_NEW_lte":10
}
asins=api.product_finder(params,domain="IT",n_products=20000)
duration=time.time()-start
date=datetime.date.today()
path=f"raw/{date:%Y/%m/%d}/asins.json"
bucket="keepa"
data=json.dumps(asins).encode()
mc=Minio(minio_endpoint,access_key=minio_access,secret_key=minio_secret,secure=False)
if not mc.bucket_exists(bucket):
    mc.make_bucket(bucket)
mc.put_object(bucket,path,io.BytesIO(data),len(data))
conn=psycopg2.connect(pg_dsn)
cur=conn.cursor()
cur.execute("INSERT INTO etl_log(date,asin_count,duration_sec) VALUES (%s,%s,%s)",(date,len(asins),duration))
conn.commit()
cur.close()
conn.close()
sys.exit(0)
