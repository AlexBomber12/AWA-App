#!/bin/bash
set -euo pipefail

REPO_URL="https://github.com/AlexBomber12/AWA-App.git"
APP_DIR="/opt/awa-app"
SERVICE_FILE="/etc/systemd/system/awa-app.service"

check_cmd() {
    command -v "$1" >/dev/null 2>&1 || { echo "$1 not installed" >&2; exit 1; }
}

check_cmd git
check_cmd docker

docker compose version >/dev/null 2>&1 || { echo "docker compose not installed" >&2; exit 1; }

if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull --ff-only
else
    git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

write_env() {
    cat > .env.postgres <<'ENV'
PG_USER=postgres
PG_PASSWORD=pass # pragma: allowlist secret
PG_DATABASE=awa
PG_HOST=postgres
PG_PORT=5432
DATABASE_URL=postgresql+asyncpg://postgres:pass@postgres:5432/awa # pragma: allowlist secret
NEXT_PUBLIC_API_URL=https://awapricer.lan/api
LLM_PROVIDER=local
MINIO_ROOT_USER=minio
MINIO_SECRET_KEY=minio123 # pragma: allowlist secret
ENV
    ln -sf .env.postgres .env
}

if [ -f .env.postgres ]; then
    read -r -p ".env.postgres exists – overwrite? [y/N] " ans
    if [[ $ans =~ ^[Yy]$ ]]; then
        write_env
    fi
else
    write_env
fi

if [ -f web/.env ]; then
    sed -Ei 's#^(VITE_API_URL|NEXT_PUBLIC_API_URL)=.*#\1=https://awapricer.lan/api#' web/.env
else
    echo "VITE_API_URL=https://awapricer.lan/api" > web/.env
fi

docker compose pull && docker compose build && docker compose up -d --wait || exit 1

curl -fs https://awapricer.lan/api/health >/dev/null || { echo "Health check failed" >&2; exit 1; }

if [ ! -f "$SERVICE_FILE" ]; then
    read -r -p "Create systemd service? [y/N] " ans
    if [[ $ans =~ ^[Yy]$ ]]; then
        cat > "$SERVICE_FILE" <<UNIT
[Unit]
Description=AWA App Stack
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose up -d --wait
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
UNIT
        systemctl daemon-reload
        systemctl enable awa-app.service
    fi
fi

echo "Stack deployed — open https://awapricer.lan"
