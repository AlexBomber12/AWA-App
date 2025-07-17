from __future__ import annotations

import datetime
import os
from typing import Any

import boto3
from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import JSONResponse

from etl import load_csv

BUCKET = "awa-bucket"

router = APIRouter()


def get_minio() -> Any:
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    access = os.getenv("MINIO_ACCESS_KEY", "minio")
    secret = os.getenv("MINIO_SECRET_KEY", "minio123")
    return boto3.client(
        "s3",
        endpoint_url=f"http://{endpoint}",
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name="us-east-1",
    )


@router.post("/", status_code=201)
async def upload(file: UploadFile, minio: Any = Depends(get_minio)) -> JSONResponse:
    today = datetime.date.today().strftime("%Y-%m")
    dst = f"raw/amazon/{today}/{file.filename}"
    minio.put_object(Bucket=BUCKET, Key=dst, Body=file.file)
    _, inserted = load_csv.main(["--source", f"minio://{dst}", "--table", "auto"])
    return JSONResponse(status_code=201, content={"inserted_rows": inserted, "status": "success"})
