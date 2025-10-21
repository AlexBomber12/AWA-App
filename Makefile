SHELL := /usr/bin/env bash

.PHONY: up down logs sh fmt lint test unit integ bootstrap ci-local migrations-local integration-local ci-all doctor

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

sh:
	docker compose exec api sh -lc "bash || sh"

fmt:
	python -m black . || true

lint:
	python -m ruff check . || true

unit:
	pytest -q -m "not integration" || true

integ:
	pytest -q -m integration || true

test: unit integ

bootstrap:
	bash scripts/dev/bootstrap_wsl.sh

ci-local:
	bash scripts/ci/unit.sh

migrations-local:
	bash scripts/ci/migrations.sh

integration-local:
	bash scripts/ci/integration.sh

ci-all:
	bash scripts/ci/all.sh

doctor:
	echo "PWD=$$PWD"; python -V; which python; echo "$$WSL_DISTRO_NAME"
