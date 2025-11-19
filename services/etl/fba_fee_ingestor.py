from __future__ import annotations

import argparse
import atexit
import datetime as dt
import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, cast

import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from awa_common.dsn import build_dsn
from awa_common.etl.guard import process_once
from awa_common.etl.idempotency import build_payload_meta, compute_idempotency_key
from awa_common.http_client import HTTPClient
from awa_common.metrics import record_etl_run, record_etl_skip
from awa_common.settings import settings

logger = structlog.get_logger(__name__)

DEFAULT_ASINS = ("DUMMY1", "DUMMY2")
DEFAULT_FIXTURE_PATH = Path("tests/fixtures/helium_fees_sample.json")
SOURCE_NAME = "fba_fee_ingestor"
HELIUM_ENDPOINT = "https://api.helium10.com/v1/profits/fees"


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
    etl_cfg = getattr(settings, "etl", None)
    return bool(etl_cfg.enable_live if etl_cfg else False)


_HTTP_CLIENT = HTTPClient(integration=SOURCE_NAME)
atexit.register(_HTTP_CLIENT.close)


def _request_helium_fee(url: str, headers: dict[str, str]) -> dict[str, Any]:
    return cast(dict[str, Any], _HTTP_CLIENT.get_json(url, headers=headers))


def fetch_live_fees(asins: Iterable[str], api_key: str, *, task_id: str | None) -> list[tuple[str, float]]:
    if not api_key:
        raise RuntimeError("Missing HELIUM_API_KEY")
    results: list[tuple[str, float]] = []
    headers = {"Authorization": f"Bearer {api_key}"}
    for asin in asins:
        url = f"{HELIUM_ENDPOINT}?asin={asin}"
        data = _request_helium_fee(url, headers)
        results.append((asin, float(data["totalFbaFee"])))
    return results


def load_offline_fees(path: Path) -> list[tuple[str, float]]:
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    return [(entry["asin"], float(entry["totalFbaFee"])) for entry in data]


def ensure_table(session: Session) -> None:
    session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS fees_raw (
                asin TEXT PRIMARY KEY,
                fee NUMERIC,
                captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )


def upsert_fees(session: Session, rows: list[tuple[str, float]]) -> None:
    if not rows:
        logger.info("etl.no_data", source=SOURCE_NAME)
        return
    session.execute(
        text(
            """
            INSERT INTO fees_raw (asin, fee)
            VALUES (:asin, :fee)
            ON CONFLICT (asin)
            DO UPDATE SET
                fee = EXCLUDED.fee,
                captured_at = NOW()
            """
        ),
        [{"asin": asin, "fee": fee} for asin, fee in rows],
    )


def build_idempotency(
    live: bool, *, asins: Sequence[str], fixture_path: Path | None = None
) -> tuple[str, dict[str, Any]]:
    if live:
        today = dt.date.today().isoformat()
        payload = json.dumps(
            {"mode": "live", "date": today, "asins": sorted(asins)},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        key = compute_idempotency_key(content=payload)
        meta = build_payload_meta(
            remote_meta=None,
            source_url=HELIUM_ENDPOINT,
            extra={"mode": "live", "asin_count": len(asins), "date": today},
        )
        return key, meta
    if fixture_path is None:
        raise ValueError("fixture_path required for offline mode")
    key = compute_idempotency_key(path=fixture_path)
    meta = build_payload_meta(path=fixture_path, extra={"mode": "offline"})
    return key, meta


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else [])
    live = resolve_live(args.live)
    fixture_path = Path(args.fixture_path)
    idempotency_key, payload_meta = build_idempotency(
        live,
        asins=args.asins,
        fixture_path=fixture_path if not live else None,
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

            session = handle.session
            with record_etl_run(SOURCE_NAME):
                ensure_table(session)
                if live:
                    rows = fetch_live_fees(
                        args.asins,
                        getattr(getattr(settings, "etl", None), "helium_api_key", ""),
                        task_id=task_id,
                    )
                else:
                    rows = load_offline_fees(fixture_path)
                upsert_fees(session, rows)
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
