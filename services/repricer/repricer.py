import os
import asyncio
import asyncpg
import aiosqlite
from sp_api.api import Listings


query = """
    SELECT offer_id, asin, target_min
    FROM offers
    WHERE buybox_price > target_min AND buybox_price < target_max
"""


async def main():
    dsn = os.environ["DATABASE_URL"]
    if dsn.startswith("sqlite"):
        db = await aiosqlite.connect(dsn.replace("sqlite:///", ""))
        db.row_factory = aiosqlite.Row
        async with db.execute(query) as cur:
            rows = await cur.fetchall()
    else:
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
        if dsn.startswith("sqlite"):
            await db.execute(
                "INSERT INTO repricer_log (offer_id, new_price) VALUES (?, ?)",
                (r["offer_id"], r["target_min"]),
            )
        else:
            await pool.execute(
                "INSERT INTO repricer_log (offer_id, new_price) VALUES ($1, $2)",
                r["offer_id"],
                r["target_min"],
            )
    if dsn.startswith("sqlite"):
        await db.commit()
        await db.close()
    else:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
