from __future__ import annotations

import argparse
import json
import logging
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import httpx
from awa_common.dsn import build_dsn
from sqlalchemy import create_engine

from services.fees_h10 import repository as repo

DEFAULT_FIXTURE_PATH = Path("tests/fixtures/spapi_fees_sample.json")
DEFAULT_SKUS = ("DUMMY1", "DUMMY2")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest Amazon SP API fee estimates into the fees_raw table.",
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
        "--skus",
        nargs="+",
        default=list(DEFAULT_SKUS),
        help="List of SKUs to process (default: %(default)s).",
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


def build_rows_from_live(
    skus: Sequence[str],
    *,
    refresh_token: str,
    client_id: str,
    client_secret: str,
    region: str,
) -> list[dict[str, Any]]:
    from typing import cast

    from sp_api.api import SellingPartnerAPI

    client_factory = cast(Any, SellingPartnerAPI)
    api = cast(
        Any,
        client_factory(
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            region=region,
        ),
    )
    rows: list[dict[str, Any]] = []
    for asin in skus:
        response = api.get_my_fees_estimate_for_sku(asin)
        amount = response["payload"]["FeesEstimateResult"]["FeesEstimate"][
            "TotalFeesEstimate"
        ]["Amount"]
        rows.append(
            {
                "asin": asin,
                "marketplace": region or "US",
                "fee_type": "fba_pick_pack",
                "amount": amount,
                "currency": "USD",
                "source": "sp",
                "effective_date": os.getenv("SP_FEES_DATE"),
            }
        )
    return rows


def build_rows_from_fixture(path: Path) -> list[dict[str, Any]]:
    with path.open() as fp:
        data = json.load(fp)
    rows: list[dict[str, Any]] = []
    for entry in data:
        rows.append(
            {
                "asin": entry["asin"],
                "marketplace": "US",
                "fee_type": "fba_pick_pack",
                "amount": entry["payload"]["FeesEstimateResult"]["FeesEstimate"][
                    "TotalFeesEstimate"
                ]["Amount"],
                "currency": "USD",
                "source": "sp",
                "effective_date": entry.get("date"),
            }
        )
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else [])
    live = resolve_live(args.live)
    dsn = build_dsn()
    rows: list[dict[str, Any]]
    try:
        if live:
            rows = build_rows_from_live(
                args.skus,
                refresh_token=os.getenv("SP_REFRESH_TOKEN", ""),
                client_id=os.getenv("SP_CLIENT_ID", ""),
                client_secret=os.getenv("SP_CLIENT_SECRET", ""),
                region=os.getenv("REGION", ""),
            )
        else:
            rows = build_rows_from_fixture(Path(args.fixture_path))
    except (
        httpx.TimeoutException,
        httpx.RequestError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        logging.error("sp fees fetch failed: %s", exc)
        return 1
    engine = create_engine(dsn)
    try:
        repo.upsert_fees_raw(engine, rows, testing=os.getenv("TESTING") == "1")
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
