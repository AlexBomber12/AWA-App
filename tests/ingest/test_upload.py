import subprocess

import boto3
import pytest
from sqlalchemy import create_engine, text

from services.common.dsn import build_dsn

pytestmark = pytest.mark.integration


class FakeS3:
    def __init__(self):
        self.store = {}

    def put_object(self, Bucket, Key, Body):
        Body.seek(0)
        self.store[Key] = Body.read()

    def download_fileobj(self, Bucket, Key, fileobj):
        fileobj.write(self.store[Key])


def test_upload(api_client, monkeypatch):
    fake = FakeS3()
    monkeypatch.setattr(boto3, "client", lambda *a, **k: fake)

    def fake_run(args, check):
        from etl import load_csv

        src = args[args.index("--source") + 1]
        load_csv.main(["--source", src, "--table", "auto"])

    monkeypatch.setattr(subprocess, "run", fake_run)

    with open("tests/fixtures/sample_prices.csv", "rb") as f:
        r = api_client.post("/upload", files={"file": ("sample.csv", f, "text/csv")})

    assert r.status_code == 201
    assert any(fake.store)

    engine = create_engine(build_dsn(sync=True))
    with engine.connect() as conn:
        row = conn.execute(text("SELECT inserted_rows, status FROM load_log"))
        result = row.fetchone()

    assert result == (2, "success")
