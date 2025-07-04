import os
import subprocess


def pytest_sessionstart(session):
    if not os.getenv("DATABASE_URL") and os.path.exists(".env.postgres"):
        with open(".env.postgres") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k, v)
    if os.getenv("DATABASE_URL"):
        try:
            subprocess.run(["alembic", "upgrade", "head"], check=True)
        except Exception:
            pass
