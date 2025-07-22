from __future__ import annotations

import asyncio

from . import client, repository


async def full(dry_run: bool = False) -> list[dict[str, object]]:
    rows = await client.fetch_rates()
    if not dry_run:
        await repository.upsert_many(rows)
    return rows


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(full(dry_run=args.dry_run))
