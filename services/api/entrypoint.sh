#!/usr/bin/env bash
/usr/bin/python - <<'PY'
import asyncio, os, asyncpg, time, sys
dsn = os.environ["DATABASE_URL"]
for _ in range(15):
    try:
        asyncio.run(asyncpg.connect(dsn)).close()
        sys.exit(0)
    except Exception:
        time.sleep(1)
print("Postgres still unavailable", file=sys.stderr)
sys.exit(1)
PY
exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
