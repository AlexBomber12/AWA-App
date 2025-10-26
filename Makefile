SHELL := /usr/bin/env bash
PYTHON ?= $(shell command -v python 2>/dev/null || command -v python3 2>/dev/null)

ifeq ($(PYTHON),)
$(error Python interpreter not found; please install python3)
endif

.PHONY: up down logs sh fmt lint type test unit unit-all integ qa qa-fix install-dev bootstrap-dev ensure-bootstrap bootstrap ci-fast ci-local migrations-local integration-local ci-all doctor

up:
	docker compose up -d --build --wait db redis api worker

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

sh:
	docker compose exec api sh -lc "bash || sh"

fmt:
	$(PYTHON) -m black . || true

lint: ensure-bootstrap
	@$(PYTHON) -m ruff check .
	@$(PYTHON) -m black --check .

type: ensure-bootstrap
	$(PYTHON) -m mypy .

unit:
	mkdir -p .local-artifacts
	PYTHONUNBUFFERED=1 pytest -vv -s -m "not integration and not slow" \
	  -n auto --dist=loadfile --durations=20 \
	| tee .local-artifacts/unit.log ; test $${PIPESTATUS[0]} -eq 0

unit-all: ensure-bootstrap
	@set -o pipefail; \
	mkdir -p .local-artifacts; \
	PYTHONUNBUFFERED=1 pytest -vv -s -m "not integration" -n auto --dist=loadfile --durations=20 2>&1 | tee .local-artifacts/pytest-unit-all.log; \
	test $${PIPESTATUS[0]} -eq 0

integ:
	pytest -q -m integration || true

bootstrap-dev:
	PIP_BREAK_SYSTEM_PACKAGES=1 $(PYTHON) -m pip install -U pip wheel
	PIP_BREAK_SYSTEM_PACKAGES=1 $(PYTHON) -m pip install -U pre-commit mypy pytest-cov
	PIP_BREAK_SYSTEM_PACKAGES=1 $(PYTHON) -m pip install -r requirements-dev.txt
	PIP_BREAK_SYSTEM_PACKAGES=1 $(PYTHON) -m pip install -e packages/awa_common
	pre-commit clean
	pre-commit install
	pre-commit install-hooks
	touch .dev_bootstrapped

ensure-bootstrap:
	@test -f .dev_bootstrapped || $(MAKE) bootstrap-dev

install-dev: bootstrap-dev

qa: ensure-bootstrap
	mkdir -p .local-artifacts
	pre-commit run --all-files --show-diff-on-failure || true
	@git diff --quiet || (echo "✖ Pre-commit modified files. Commit baseline or run 'make qa-fix'."; exit 1)
	$(MAKE) lint
	$(MAKE) type
	$(MAKE) unit

qa-fix: ensure-bootstrap
	@set -o pipefail; \
	mkdir -p .local-artifacts; \
	if [ -d .git ]; then git config --local --unset-all http.https://github.com/.extraheader || true; fi; \
	pre-commit run --all-files --show-diff-on-failure 2>&1 | tee .local-artifacts/pre-commit.log || true; \
	git add -A; \
	pre-commit run --all-files --show-diff-on-failure 2>&1 | tee .local-artifacts/pre-commit.log || true; \
	git add -A; \
	$(PYTHON) -m ruff check . --fix 2>&1 | tee .local-artifacts/ruff.log; \
	$(PYTHON) -m black . 2>&1 | tee .local-artifacts/black.log; \
	$(PYTHON) -m mypy . 2>&1 | tee .local-artifacts/mypy.log; \
	PYTHONUNBUFFERED=1 pytest -vv -s -m "not integration and not slow" -n auto --dist=loadfile --durations=20 2>&1 | tee .local-artifacts/pytest-unit.log

test: unit integ

bootstrap:
	bash scripts/dev/bootstrap_wsl.sh

ci-local:
	bash scripts/ci/unit.sh

ci-fast:
	@echo "Unit only (fast)"
	bash scripts/ci/unit.sh

migrations-local:
	bash scripts/ci/migrations.sh

integration-local:
	bash scripts/ci/integration.sh

ci-all:
	bash scripts/ci/all.sh

doctor:
	echo "PWD=$$PWD"; python -V; which python; echo "$$WSL_DISTRO_NAME"
