import os,json,datetime,time,io
import keepa
from minio import Minio
import psycopg2

live=os.getenv('ENABLE_LIVE')=='1'
key=os.environ['KEEPA_KEY']
endpoint=os.environ['MINIO_ENDPOINT']
access=os.environ['MINIO_ACCESS_KEY']
secret=os.environ['MINIO_SECRET_KEY']
pg=os.environ['PG_DSN']

start=time.monotonic()
if live:
    api=keepa.Keepa(key)
    params={'sales_rank_lte':80000,'buybox_price_gte':2000,'num_offers_lte':10}
    asins=api.product_finder(params,domain='IT',n_products=20000)
else:
    with open('fixtures/keepa_sample.json') as f:
        asins=json.load(f)
end=time.monotonic()

today=datetime.date.today()
path=f"keepa/raw/{today:%Y/%m/%d}/asins.json"
mc=Minio(endpoint,access_key=access,secret_key=secret,secure=False)
if not mc.bucket_exists('keepa'):
    mc.make_bucket('keepa')
raw=json.dumps(asins).encode()
mc.put_object('keepa',path,io.BytesIO(raw),len(raw),content_type='application/json')
conn=psycopg2.connect(pg)
conn.autocommit=True
cur=conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS etl_log(date date, asin_count integer, duration_sec real)')
cur.execute('INSERT INTO etl_log(date, asin_count, duration_sec) VALUES (%s,%s,%s)',(today,len(asins),end-start))
cur.close()
conn.close()
