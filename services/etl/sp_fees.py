from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import structlog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from awa_common.dsn import build_dsn
from awa_common.etl.guard import process_once
from awa_common.etl.idempotency import build_payload_meta, compute_idempotency_key
from awa_common.metrics import record_etl_run, record_etl_skip
from awa_common.settings import settings
from awa_common.utils.env import env_bool
from services.fees_h10 import repository as repo

logger = structlog.get_logger(__name__)

DEFAULT_FIXTURE_PATH = Path("tests/fixtures/spapi_fees_sample.json")
DEFAULT_SKUS = ("DUMMY1", "DUMMY2")
SOURCE_NAME = "sp_fees_ingestor"
_TRUTHY = {"1", "true", "t", "yes", "y", "on"}


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
    etl_cfg = getattr(settings, "etl", None)
    return bool(etl_cfg.enable_live if etl_cfg else False)


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
        response = _fetch_sp_fee(api, asin)
        total_fee = response["payload"]["FeesEstimateResult"]["FeesEstimate"]["TotalFeesEstimate"]["Amount"]
        rows.append(
            {
                "asin": asin,
                "marketplace": region or "US",
                "fee_type": "fba_pick_pack",
                "amount": total_fee,
                "currency": "USD",
                "source": "sp",
                "effective_date": getattr(getattr(settings, "etl", None), "sp_fees_date", None),
            }
        )
    return rows


def _fetch_sp_fee(api: Any, asin: str) -> dict[str, Any]:
    return cast(dict[str, Any], api.get_my_fees_estimate_for_sku(asin))


def build_rows_from_fixture(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    rows: list[dict[str, Any]] = []
    for entry in data:
        rows.append(
            {
                "asin": entry["asin"],
                "marketplace": "US",
                "fee_type": "fba_pick_pack",
                "amount": entry["payload"]["FeesEstimateResult"]["FeesEstimate"]["TotalFeesEstimate"]["Amount"],
                "currency": "USD",
                "source": "sp",
                "effective_date": entry.get("date"),
            }
        )
    return rows


def build_idempotency(
    live: bool,
    *,
    skus: Sequence[str],
    fixture_path: Path,
) -> tuple[str, dict[str, Any]]:
    if live:
        payload = json.dumps(
            {
                "mode": "live",
                "skus": sorted(skus),
                "date": getattr(getattr(settings, "etl", None), "sp_fees_date", None),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        key = compute_idempotency_key(content=payload)
        meta = build_payload_meta(
            extra={
                "mode": "live",
                "sku_count": len(skus),
                "region": getattr(getattr(settings, "etl", None), "region", None),
            }
        )
        return key, meta
    key = compute_idempotency_key(path=fixture_path)
    meta = build_payload_meta(path=fixture_path, extra={"mode": "offline"})
    return key, meta


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else [])
    live = resolve_live(args.live)
    fixture_path = Path(args.fixture_path)
    idempotency_key, payload_meta = build_idempotency(
        live,
        skus=args.skus,
        fixture_path=fixture_path,
    )
    task_id = getattr(getattr(settings, "etl", None), "task_id", None)

    engine = create_engine(build_dsn(sync=True), future=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    try:
        with process_once(
            SessionLocal,
            source=SOURCE_NAME,
            payload_meta=payload_meta,
            idempotency_key=idempotency_key,
            task_id=task_id,
        ) as handle:
            if handle is None:
                record_etl_skip(SOURCE_NAME)
                logger.info(
                    "etl.skipped",
                    source=SOURCE_NAME,
                    idempotency_key=idempotency_key,
                )
                return 0

            try:
                with record_etl_run(SOURCE_NAME):
                    if live:
                        rows = build_rows_from_live(
                            args.skus,
                            refresh_token=getattr(getattr(settings, "etl", None), "sp_refresh_token", ""),
                            client_id=getattr(getattr(settings, "etl", None), "sp_client_id", ""),
                            client_secret=getattr(getattr(settings, "etl", None), "sp_client_secret", ""),
                            region=getattr(getattr(settings, "etl", None), "region", "US"),
                        )
                    else:
                        rows = build_rows_from_fixture(fixture_path)
                    if not rows:
                        logger.info("etl.no_data", source=SOURCE_NAME)
                        return 0
                    repo.upsert_fees_raw(engine, rows, testing=_testing_enabled())
            except Exception:
                logger.exception("sp_fees.failed", source=SOURCE_NAME)
                raise
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))


def _testing_enabled() -> bool:
    env_override = os.getenv("TESTING")
    if env_override is not None:
        return bool(env_bool("TESTING", default=False))

    app_cfg = getattr(settings, "app", None)
    if app_cfg:
        return bool(app_cfg.testing)
    return bool(getattr(settings, "TESTING", False))
