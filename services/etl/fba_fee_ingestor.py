from __future__ import annotations

import argparse
import json
import os
import urllib.request
from collections.abc import Sequence
from pathlib import Path
from typing import Iterable

from awa_common.dsn import build_dsn

from pg_utils import connect

DEFAULT_ASINS = ("DUMMY1", "DUMMY2")
DEFAULT_FIXTURE_PATH = Path("tests/fixtures/helium_fees_sample.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest Helium10 FBA fee data into the fees_raw table.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live",
        dest="live",
        action="store_true",
        help="Force live execution regardless of ENABLE_LIVE=1.",
    )
    mode.add_argument(
        "--offline",
        dest="live",
        action="store_false",
        help="Force offline execution regardless of ENABLE_LIVE.",
    )
    parser.set_defaults(live=None)
    parser.add_argument(
        "--asins",
        nargs="+",
        default=list(DEFAULT_ASINS),
        help="List of ASINs to query (default: %(default)s).",
    )
    parser.add_argument(
        "--fixture-path",
        default=str(DEFAULT_FIXTURE_PATH),
        help="Path to offline fixture data (default: %(default)s).",
    )
    return parser


def resolve_live(cli_live: bool | None) -> bool:
    if cli_live is not None:
        return cli_live
    return os.getenv("ENABLE_LIVE") == "1"


def fetch_live_fees(asins: Iterable[str], api_key: str) -> list[tuple[str, float]]:
    results: list[tuple[str, float]] = []
    for asin in asins:
        url = f"https://api.helium10.com/v1/profits/fees?asin={asin}"
        request = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(request) as response:
            data = json.load(response)
        results.append((asin, data["totalFbaFee"]))
    return results


def load_offline_fees(path: Path) -> list[tuple[str, float]]:
    with path.open() as fp:
        data = json.load(fp)
    return [(entry["asin"], entry["totalFbaFee"]) for entry in data]


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else [])
    live = resolve_live(args.live)
    dsn = build_dsn()
    if live:
        results = fetch_live_fees(args.asins, os.getenv("HELIUM_API_KEY", ""))
    else:
        results = load_offline_fees(Path(args.fixture_path))
    conn = connect(dsn)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS fees_raw CASCADE")
    cur.execute(
        "CREATE TABLE fees_raw(asin text primary key, fee numeric, captured_at timestamptz default now())"
    )
    for asin, fee in results:
        cur.execute(
            "INSERT INTO fees_raw(asin, fee) VALUES (%s,%s) ON CONFLICT (asin) DO UPDATE SET fee = EXCLUDED.fee",
            (asin, fee),
        )
    conn.commit()
    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
