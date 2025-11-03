from email.message import EmailMessage

from services.worker import email_watcher


class DummyS3:
    def __init__(self):
        self.uploads = []

    def upload_file(self, tmp_path, bucket, key):
        self.uploads.append((tmp_path, bucket, key))


class DummyEngine:
    def __init__(self):
        self.executed = []

    def begin(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, stmt, params):
        self.executed.append((str(stmt), params))

    def dispose(self):
        return None


class DummyIMAP:
    def __init__(self, message_bytes):
        self.message_bytes = message_bytes
        self.flags = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def login(self, user, password):
        assert user == "user"
        assert password == "pass"

    def select_folder(self, name):
        assert name == "INBOX"

    def search(self, criteria):
        return [1]

    def fetch(self, uid, fields):
        return {uid: {b"RFC822": self.message_bytes}}

    def add_flags(self, uid, flags):
        self.flags.append((uid, flags))


def test_email_watcher_main(monkeypatch):
    monkeypatch.setenv("IMAP_HOST", "imap.local")
    monkeypatch.setenv("IMAP_USER", "user")
    monkeypatch.setenv("IMAP_PASS", "pass")
    monkeypatch.setenv("MINIO_ENDPOINT", "minio:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "ak")
    monkeypatch.setenv("MINIO_SECRET_KEY", "sk")

    msg = EmailMessage()
    msg["From"] = "test@example.com"
    msg["To"] = "dest@example.com"
    msg.set_content("body")
    msg.add_attachment(b"col\n1\n", maintype="text", subtype="csv", filename="report.csv")
    raw = msg.as_bytes()

    dummy_s3 = DummyS3()
    monkeypatch.setattr(email_watcher.boto3, "client", lambda *_args, **_kwargs: dummy_s3)
    dummy_engine = DummyEngine()
    monkeypatch.setattr(email_watcher, "create_engine", lambda *_: dummy_engine)
    monkeypatch.setattr(email_watcher.load_csv, "main", lambda args: ("load-1", 2))
    monkeypatch.setattr(email_watcher, "IMAPClient", lambda host: DummyIMAP(raw))

    result = email_watcher.main()
    assert result == {"status": "success"}
    assert dummy_s3.uploads, "expected upload to be called"
    assert dummy_engine.executed[0][1]["n"] == 2
