from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_etl(api_key: str, minio_client: Any, etl_log: Any, tmp_path: Path) -> Path:
    import keepa

    k = keepa.Keepa(api_key)
    data = k.product_finder({"domainId": 1})
    file_path = tmp_path / "data.json"
    with open(file_path, "w") as f:
        json.dump(data, f)
    minio_client.fput_object("bucket", "data.json", str(file_path))
    etl_log.insert({"file": str(file_path)})
    return file_path
