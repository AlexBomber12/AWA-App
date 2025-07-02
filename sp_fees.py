import os
from sp_api.api import SellingPartnerAPI
import psycopg2


def pg_dsn() -> str:
    if "PG_DSN" in os.environ:
        return os.environ["PG_DSN"]
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "pass")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "postgres")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def main():
    live = os.getenv("ENABLE_LIVE") == "1"
    dsn = pg_dsn()
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
