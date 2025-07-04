#!/bin/bash
set -e

url="${DATABASE_URL}"
if [ -z "$url" ]; then
  echo "DATABASE_URL not set" >&2
  exit 1
fi

read host port <<PYEOF
$(python - <<'PY'
import os, urllib.parse
u=os.environ['DATABASE_URL']
u=u.replace('postgresql+asyncpg://','postgresql://').replace('postgresql+psycopg://','postgresql://')
parsed=urllib.parse.urlparse(u)
print(parsed.hostname)
print(parsed.port or 5432)
PY
)
PYEOF

delay=1
elapsed=0
while ! pg_isready -h "$host" -p "$port" >/dev/null 2>&1; do
  sleep "$delay"
  elapsed=$((elapsed + delay))
  if [ $elapsed -ge 30 ]; then
    echo "Database not reachable after ${elapsed}s" >&2
    exit 1
  fi
  if [ $delay -lt 8 ]; then
    delay=$((delay * 2))
  fi
done

alembic upgrade head
exec uvicorn services.api.main:app --host 0.0.0.0 --port 8000
