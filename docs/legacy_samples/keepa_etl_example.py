"""
Legacy Keepa ETL example preserved for documentation only.

This file deliberately lives outside the runtime packages so it cannot be
imported by services; it is purely a historical reference.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_etl(api_key: str, minio_client: Any, etl_log: Any, tmp_path: Path) -> Path:
    """
    Minimal Keepa-driven ETL example retained for historical context.

    The production ingestion stack now lives under services/, so treat this
    snippet as reference material rather than callable code.
    """

    import keepa  # type: ignore import-not-found

    keepa_client = keepa.Keepa(api_key)
    data = keepa_client.product_finder({"domainId": 1})
    file_path = tmp_path / "data.json"
    with file_path.open("w") as handle:
        json.dump(data, handle)
    minio_client.fput_object("bucket", "data.json", str(file_path))
    etl_log.insert({"file": str(file_path)})
    return file_path
