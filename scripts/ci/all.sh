#!/usr/bin/env bash
set -euo pipefail

export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

mkdir -p .local-artifacts

docker compose up -d --build --wait db redis

bash scripts/ci/unit.sh
bash scripts/ci/migrations.sh

docker compose up -d --build --wait api worker

echo "Waiting for API and worker readiness"
READY=0
for i in $(seq 1 60); do
  if curl -fsS http://localhost:8000/ready >/dev/null 2>&1 && \
     curl -fsS http://localhost:8001/ready >/dev/null 2>&1; then
    echo "Services ready after $i attempt(s)"
    READY=1
    break
  fi
  sleep 2
done

if [ "$READY" -ne 1 ]; then
  echo "Services did not become ready within timeout" >&2
  docker compose logs api worker | tail -n 200 || true
  exit 1
fi

bash scripts/ci/integration.sh
echo "LOCAL CI OK"
