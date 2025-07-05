from __future__ import annotations

import argparse

from .reader import load_file
from .normaliser import normalise
from .repository import Repository


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import vendor price sheet")
    parser.add_argument("file")
    parser.add_argument("--vendor", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    df = load_file(args.file)
    df = normalise(df)
    repo = Repository()
    vendor_id = repo.ensure_vendor(args.vendor)
    rows = df.to_dict(orient="records")
    inserted, updated = repo.upsert_prices(vendor_id, rows, dry_run=args.dry_run)
    print(f"processed={len(rows)} inserted={inserted} updated={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
