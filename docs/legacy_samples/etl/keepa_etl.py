from __future__ import annotations

import argparse
import datetime
import io
import json
import time
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from awa_common.dsn import build_dsn
from awa_common.settings import settings
from pg_utils import connect

DEFAULT_FIXTURE_PATH = Path("fixtures/keepa_sample.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Keepa ETL job to load ASIN data into MinIO and Postgres.",
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
    return parser


def resolve_live(cli_live: bool | None) -> bool:
    if cli_live is not None:
        return cli_live
    etl_cfg = getattr(settings, "etl", None)
    return bool(etl_cfg.enable_live if etl_cfg else False)


def load_live_data(key: str) -> bytes:
    import keepa

    api = keepa.Keepa(key)
    params = {
        "current_SALES_lte": 80000,
        "current_BUY_BOX_SHIPPING_gte": 2000,
        "current_COUNT_NEW_lte": 10,
    }
    payload = api.product_finder(params, domain="IT", n_products=20000)
    return json.dumps(payload).encode()


def load_offline_data(path: Path) -> bytes:
    with path.open() as fp:
        payload = json.load(fp)
    return json.dumps(payload).encode()


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else [])
    live = resolve_live(args.live)
    etl_cfg = getattr(settings, "etl", None)
    key = etl_cfg.keepa_key if etl_cfg else None
    s3_cfg = getattr(settings, "s3", None)
    endpoint = s3_cfg.endpoint if s3_cfg else None
    access = s3_cfg.access_key if s3_cfg else None
    secret = s3_cfg.secret_key if s3_cfg else None
    secure = bool(s3_cfg.secure) if s3_cfg else False
    if live and not key:
        raise RuntimeError("KEEPA_KEY not set")
    if not endpoint or not access or not secret:
        raise RuntimeError("MINIO credentials are not fully configured")
    dsn = build_dsn()
    start = time.time()
    if live:
        key_value = cast(str, key)
        data = load_live_data(key_value)
    else:
        data = load_offline_data(Path(args.fixture_path))
    duration = time.time() - start
    today = datetime.date.today()
    bucket = "keepa"
    path = f"raw/{today:%Y/%m/%d}/asins.json"
    from minio import Minio

    mc = Minio(endpoint, access_key=access, secret_key=secret, secure=secure)
    if not mc.bucket_exists(bucket):
        mc.make_bucket(bucket)
    mc.put_object(bucket, path, io.BytesIO(data), len(data))
    conn = connect(dsn)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO etl_log(date,asin_count,duration_sec) VALUES (%s,%s,%s)",
        (today, len(json.loads(data)), duration),
    )
    conn.commit()
    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
