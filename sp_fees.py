import os
from sp_api.api import SellingPartnerAPI
import psycopg2


def main():
    live = os.getenv("ENABLE_LIVE") == "1"
    dsn = os.environ["PG_DSN"]
    conn = psycopg2.connect(dsn)
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
