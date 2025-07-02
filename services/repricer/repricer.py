import os
import asyncio
import asyncpg
from sp_api.api import Listings


def pg_dsn() -> str:
    if "PG_DSN" in os.environ:
        return os.environ["PG_DSN"]
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "pass")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "postgres")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


query = """
    SELECT offer_id, asin, target_min
    FROM offers
    WHERE buybox_price > target_min AND buybox_price < target_max
"""


async def main():
    dsn = pg_dsn()
    pool = await asyncpg.create_pool(dsn)
    rows = await pool.fetch(query)
    listings = Listings(
        credentials={
            "refresh_token": os.environ["SP_REFRESH_TOKEN"],
            "lwa_app_id": os.environ["SP_CLIENT_ID"],
            "lwa_client_secret": os.environ["SP_CLIENT_SECRET"],
        }
    )
    for r in rows:
        listings.pricing(asin=r["asin"], price=r["target_min"])
        await pool.execute(
            "INSERT INTO repricer_log (offer_id, new_price) VALUES ($1, $2)",
            r["offer_id"],
            r["target_min"],
        )
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
