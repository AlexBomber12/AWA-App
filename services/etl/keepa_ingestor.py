from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from awa_common.dsn import build_dsn

from pg_utils import connect

DEFAULT_FIXTURE_PATH = Path("tests/fixtures/keepa_sample.json")
DEFAULT_OFFLINE_PATH = Path("tmp/offline_asins.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Keepa ingestor in live or offline mode.",
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
        "--fixture-path",
        default=str(DEFAULT_FIXTURE_PATH),
        help="Path to offline fixture data (default: %(default)s).",
    )
    parser.add_argument(
        "--offline-output",
        default=str(DEFAULT_OFFLINE_PATH),
        help="Where to write offline output JSON (default: %(default)s).",
    )
    return parser


def resolve_live(cli_live: bool | None) -> bool:
    if cli_live is not None:
        return cli_live
    return os.getenv("ENABLE_LIVE") == "1"


def load_offline_fixture(path: Path) -> list[dict[str, Any]]:
    with path.open() as fp:
        data = json.load(fp)
    return cast(list[dict[str, Any]], data)


def write_offline_fixture(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else [])
    live = resolve_live(args.live)
    key = os.getenv("KEEPA_KEY")
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    access = os.getenv("MINIO_ACCESS_KEY", "minio")
    secret = os.getenv("MINIO_SECRET_KEY", "minio123")
    dsn = build_dsn()
    start = time.time()
    if live:
        import keepa

        if not key:
            raise RuntimeError("KEEPA_KEY not set")
        api = keepa.Keepa(key)
        params = {
            "sales_rank_lte": 80000,
            "buybox_price_gte": 2000,
            "num_offers_lte": 10,
        }
        asins = api.product_finder(params, domain="IT", n_products=20000)
    else:
        fixture_path = Path(args.fixture_path)
        asins = load_offline_fixture(fixture_path)
    duration = time.time() - start
    today = datetime.date.today()
    if live:
        from minio import Minio

        path = f"raw/{today:%Y/%m/%d}/asins.json"
        mc = Minio(endpoint, access_key=access, secret_key=secret, secure=False)
        if not mc.bucket_exists("keepa"):
            mc.make_bucket("keepa")
        data = json.dumps(asins).encode()
        mc.put_object("keepa", path, io.BytesIO(data), len(data), content_type="application/json")
        conn = connect(dsn)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS etl_log(date date, asin_count int, duration_sec real)"
        )
        cur.execute(
            "INSERT INTO etl_log(date, asin_count, duration_sec) VALUES (%s,%s,%s)",
            (today, len(asins), duration),
        )
        cur.close()
        conn.close()
    else:
        offline_path = Path(args.offline_output)
        write_offline_fixture(offline_path, asins)
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
