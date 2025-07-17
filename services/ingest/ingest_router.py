from __future__ import annotations

import subprocess

from fastapi import APIRouter, Query

router = APIRouter()


@router.post("/ingest")
def ingest(path: str = Query(..., alias="path")) -> dict[str, str]:
    subprocess.run(["python", "-m", "etl.load_csv", "--source", f"minio://{path}", "--table", "auto"], check=True)
    return {"status": "ok"}
