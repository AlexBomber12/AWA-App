import os
import requests
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
    skus = ["DUMMY1", "DUMMY2"]
    if live:
        for sku in skus:
            r = requests.get(f"https://api.example.com/{sku}")
            cur.execute("INSERT INTO fees_raw VALUES (%s, %s)", (sku, r.json()))
    else:
        for sku in skus:
            cur.execute("INSERT INTO fees_raw VALUES (%s, %s)", (sku, "{}"))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
