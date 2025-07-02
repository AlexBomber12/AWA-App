#!/bin/bash

# Section 3: create offline .env
cat > .env <<'ENV'
MINIO_ROOT_USER=minio
MINIO_SECRET_KEY=minio123
NEXT_PUBLIC_API_URL=http://localhost:8000
DATABASE_URL=sqlite+aiosqlite:///data/awa.db
ENV
