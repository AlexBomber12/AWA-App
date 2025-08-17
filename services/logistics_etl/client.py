import csv
import io
import os

import httpx
from httpx import HTTPError

URL = os.getenv("FREIGHT_API_URL", "https://example.com/freight.csv")


async def fetch_rates() -> list[dict]:
    async with httpx.AsyncClient(timeout=15, trust_env=False) as client:
        try:
            r = await client.get(URL)
            r.raise_for_status()
        except HTTPError:
            return []
        buf = io.StringIO(r.text)
        reader = csv.DictReader(buf)
        rows = []
        for row in reader:
            row["eur_per_kg"] = float(row.get("eur_per_kg", 0))
            rows.append(row)
        return rows
