#!/bin/sh
set -e
host="$1"
shift
until python - "$host" <<'PY'
import sys,socket,time
h,p=sys.argv[1].split(":")
for _ in range(30):
    try:
        with socket.create_connection((h,int(p)),timeout=1):
            sys.exit(0)
    except OSError:
        time.sleep(1)
PY

do
  echo "Waiting for $host..."
  sleep 1
done
exec "$@"

