from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import time
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

import structlog
from minio import Minio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from awa_common.dsn import build_dsn
from awa_common.etl.guard import process_once
from awa_common.etl.idempotency import build_payload_meta, compute_idempotency_key
from awa_common.metrics import record_etl_run, record_etl_skip
from awa_common.settings import settings

logger = structlog.get_logger(__name__)

DEFAULT_FIXTURE_PATH = Path("tests/fixtures/keepa_sample.json")
DEFAULT_OFFLINE_PATH = Path("tmp/offline_asins.json")
SOURCE_NAME = "keepa_ingestor"


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
    etl_cfg = getattr(settings, "etl", None)
    return bool(etl_cfg.enable_live if etl_cfg else False)


def load_offline_fixture(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    return list(data)


def write_offline_fixture(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def build_idempotency(
    live: bool,
    *,
    fixture_path: Path,
    offline_output: Path,
) -> tuple[str, dict[str, Any]]:
    if live:
        today = dt.date.today().isoformat()
        payload = json.dumps(
            {"mode": "live", "date": today},
            separators=(",", ":"),
        ).encode("utf-8")
        key = compute_idempotency_key(content=payload)
        meta = build_payload_meta(
            extra={"mode": "live", "date": today, "bucket": "keepa"},
        )
        return key, meta
    key = compute_idempotency_key(path=fixture_path)
    meta = build_payload_meta(
        path=fixture_path,
        extra={
            "mode": "offline",
            "offline_output": str(offline_output),
        },
    )
    return key, meta


class _KeepaClient(Protocol):
    def product_finder(
        self,
        parameters: dict[str, Any],
        *,
        domain: str,
        n_products: int,
    ) -> list[Any]: ...


if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from keepa import Keepa as _Keepa  # noqa: F401


def _load_keepa_client(key: str) -> _KeepaClient:
    import keepa

    client = keepa.Keepa(key)
    return cast(_KeepaClient, client)


def _fetch_live_asins(key: str, *, task_id: str | None) -> list[Any]:
    api = _load_keepa_client(key)
    params = {
        "sales_rank_lte": 80000,
        "buybox_price_gte": 2000,
        "num_offers_lte": 10,
    }
    return list(api.product_finder(params, domain="IT", n_products=20000))


def _upload_to_minio(data: bytes, *, endpoint: str, access: str, secret: str) -> str:
    client = Minio(endpoint, access_key=access, secret_key=secret, secure=False)
    if not client.bucket_exists("keepa"):
        client.make_bucket("keepa")
    today = dt.date.today()
    path = f"raw/{today:%Y/%m/%d}/asins.json"
    client.put_object(
        "keepa",
        path,
        io.BytesIO(data),
        len(data),
        content_type="application/json",
    )
    return path


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else [])
    live = resolve_live(args.live)
    fixture_path = Path(args.fixture_path)
    offline_output = Path(args.offline_output)
    idempotency_key, payload_meta = build_idempotency(
        live,
        fixture_path=fixture_path,
        offline_output=offline_output,
    )
    etl_cfg = getattr(settings, "etl", None)
    task_id = etl_cfg.task_id if etl_cfg else None

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

            start = time.perf_counter()
            with record_etl_run(SOURCE_NAME):
                if live:
                    keepa_key = etl_cfg.keepa_key if etl_cfg else None
                    if not keepa_key:
                        raise RuntimeError("KEEPA_KEY not set")
                    asins = _fetch_live_asins(keepa_key, task_id=task_id)
                    data = json.dumps(asins).encode("utf-8")
                    minio_path = _upload_to_minio(
                        data,
                        endpoint=getattr(getattr(settings, "s3", None), "endpoint", "minio:9000"),
                        access=getattr(getattr(settings, "s3", None), "access_key", "minio"),
                        secret=getattr(getattr(settings, "s3", None), "secret_key", "minio123"),
                    )
                    logger.info(
                        "keepa.uploaded",
                        source=SOURCE_NAME,
                        minio_key=minio_path,
                        asin_count=len(asins),
                        duration_s=time.perf_counter() - start,
                    )
                else:
                    asins = load_offline_fixture(fixture_path)
                    write_offline_fixture(offline_output, asins)
                    logger.info(
                        "keepa.offline_written",
                        source=SOURCE_NAME,
                        output=str(offline_output),
                        asin_count=len(asins),
                    )
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
