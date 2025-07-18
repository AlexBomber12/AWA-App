import email
import os

import boto3
import pytest
from sqlalchemy import create_engine, text

from services.common.dsn import build_dsn
from services.ingest import email_watcher

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


class FakeS3:
    def __init__(self):
        self.store = {}

    def upload_file(self, filename, bucket, key):
        with open(filename, "rb") as f:
            self.store[key] = f.read()

    def download_fileobj(self, Bucket, Key, fileobj):
        fileobj.write(self.store[Key])


class FakeIMAP:
    def __init__(self, msg_bytes):
        self.msg_bytes = msg_bytes
        self.seen = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def login(self, u, p):
        pass

    def select_folder(self, f):
        pass

    def search(self, crit):
        return [1]

    def fetch(self, uid, parts):
        return {1: {b"RFC822": self.msg_bytes}}

    def add_flags(self, uid, flags):
        self.seen = True


def test_email_watcher(monkeypatch, pg_pool, tmp_path):
    fake_s3 = FakeS3()
    monkeypatch.setattr(boto3, "client", lambda *a, **k: fake_s3)

    msg = email.message.EmailMessage()
    msg["From"] = "x@example.com"
    msg["To"] = "y@example.com"
    msg["Subject"] = "Report"
    with open("tests/fixtures/sample_prices.csv", "rb") as f:
        msg.add_attachment(
            f.read(), filename="report.csv", maintype="text", subtype="csv"
        )

    monkeypatch.setattr(
        email_watcher, "IMAPClient", lambda host: FakeIMAP(msg.as_bytes())
    )

    os.environ["IMAP_HOST"] = "x"
    os.environ["IMAP_USER"] = "u"
    os.environ["IMAP_PASS"] = "p"

    result = email_watcher.main()
    assert result == {"status": "success"}

    assert any(fake_s3.store)

    engine = create_engine(build_dsn(sync=True))
    with engine.connect() as conn:
        row = conn.execute(text("SELECT status FROM load_log"))
        result = row.fetchone()
    assert result[0] == "success"
