import csv
import io
import os

import httpx

URL = os.getenv("FREIGHT_API_URL", "https://example.com/freight.csv")


async def fetch_rates() -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(URL)
        r.raise_for_status()
        buf = io.StringIO(r.text)
        reader = csv.DictReader(buf)
        rows = []
        for row in reader:
            row["eur_per_kg"] = float(row.get("eur_per_kg", 0))
            rows.append(row)
        return rows
