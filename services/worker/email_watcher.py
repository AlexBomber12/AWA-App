import datetime
import email
import os
import tempfile
from typing import Any

from imapclient import IMAPClient
from sqlalchemy import create_engine, text

from awa_common.minio import create_boto3_client, get_bucket_name
from awa_common.settings import settings
from services.etl import load_csv

BUCKET = get_bucket_name()


def main() -> dict[str, str]:
    """Upload CSV/XLSX attachments to MinIO and trigger ingestion.

    Returns {"status": "success"} when processing completes.
    """
    email_cfg = getattr(settings, "email", None)
    host = os.getenv("IMAP_HOST") or (email_cfg.host if email_cfg else None)
    user = os.getenv("IMAP_USER") or (email_cfg.username if email_cfg else None)
    password = os.getenv("IMAP_PASS") or (email_cfg.password if email_cfg else None)
    if not host or not user or not password:
        raise RuntimeError("IMAP configuration is missing")
    s3 = create_boto3_client()

    with IMAPClient(host) as client:
        client.login(user, password)
        client.select_folder("INBOX")
        for uid in client.search(["UNSEEN"]):
            msg_bytes = client.fetch(uid, ["RFC822"])[uid][b"RFC822"]
            msg = email.message_from_bytes(msg_bytes)
            for part in msg.walk():
                name = part.get_filename()
                if not name:
                    continue
                if not (name.endswith(".csv") or name.endswith(".xlsx")):
                    continue
                data: Any = part.get_payload(decode=True)
                if not isinstance(data, bytes | bytearray):
                    data = b""
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(data)
                    tmp_path = tmp.name
                today = datetime.date.today().strftime("%Y-%m")
                dst = f"raw/amazon/{today}/{name}"
                s3.upload_file(tmp_path, BUCKET, dst)
                load_id, inserted = load_csv.main(["--source", f"minio://{dst}", "--table", "auto"])
                engine = create_engine(settings.DATABASE_URL)
                with engine.begin() as db:
                    db.execute(
                        text("UPDATE load_log SET status='success', inserted_rows=:n WHERE id=:id"),
                        {"n": inserted, "id": load_id},
                    )
                engine.dispose()
                os.remove(tmp_path)
            client.add_flags(uid, ["\\Seen"])
    return {"status": "success"}


if __name__ == "__main__":
    main()
