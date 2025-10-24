import datetime
from io import BytesIO

from fastapi import UploadFile

from services.api.routes import upload as upload_module


class DummyMinio:
    def __init__(self):
        self.calls = []

    def put_object(self, Bucket, Key, Body):  # noqa: N802  - external API
        data = Body.read() if hasattr(Body, "read") else Body
        self.calls.append((Bucket, Key, data))


async def test_upload_writes_to_minio(monkeypatch):
    dummy = DummyMinio()
    monkeypatch.setattr(upload_module.load_csv, "main", lambda args: ("id", 5))
    real_date = datetime.date

    class DateStub:
        @staticmethod
        def today():
            return real_date(2024, 1, 1)

    monkeypatch.setattr(upload_module.datetime, "date", DateStub)
    upload = UploadFile(filename="report.csv", file=BytesIO(b"col\n1\n"))
    response = await upload_module.upload(upload, minio=dummy)
    assert response.status_code == 201
    assert dummy.calls[0][1].startswith("raw/amazon/2024-01")
