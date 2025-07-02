import os
from sp_api.api import SellingPartnerAPI
import sqlite3
import psycopg2
from db import pg_dsn


def main():
    live = os.getenv("ENABLE_LIVE") == "1"
    dsn = pg_dsn()
    if dsn.startswith("sqlite"):
        conn = sqlite3.connect(dsn.replace("sqlite:///", ""))
        cur = conn.cursor()
    else:
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
    skus = ["SKU1", "SKU2"]
    if live:
        api = SellingPartnerAPI()
        for sku in skus:
            data = api.get_my_fees_estimate_for_sku(seller_sku=sku)
            if dsn.startswith("sqlite"):
                cur.execute("INSERT INTO fees_raw VALUES (?, ?)", (sku, data))
            else:
                cur.execute("INSERT INTO fees_raw VALUES (%s, %s)", (sku, data))
    else:
        for sku in skus:
            if dsn.startswith("sqlite"):
                cur.execute("INSERT INTO fees_raw VALUES (?, ?)", (sku, "{}"))
            else:
                cur.execute("INSERT INTO fees_raw VALUES (%s, %s)", (sku, "{}"))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
