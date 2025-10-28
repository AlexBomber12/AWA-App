SHELL := /bin/bash
.ONESHELL:

ART := .local-artifacts

# Interpreter discovery (prefer repo venv, then python3, then python)
VENV_PY := $(CURDIR)/.venv/bin/python
ifeq ($(wildcard $(VENV_PY)),)
  PY := $(shell command -v python3 2>/dev/null)
  ifeq ($(PY),)
    PY := $(shell command -v python 2>/dev/null)
  endif
else
  PY := $(VENV_PY)
  PATH := $(CURDIR)/.venv/bin:$(PATH)
endif

# Fail early with a helpful message if no interpreter was found
ifeq ($(PY),)
  $(error No Python interpreter found. Activate your virtualenv or install Python 3.11; e.g. `pyenv local 3.11.9` or `python3 -m venv .venv && . .venv/bin/activate`)
endif

PIP := $(PY) -m pip
PYTEST := $(PY) -m pytest
MYPY := $(PY) -m mypy
RUFF := $(PY) -m ruff
BLACK := $(PY) -m black

.PHONY: up down logs sh fmt lint type test unit unit-all integ qa qa-fix install-dev bootstrap-dev ensure-bootstrap bootstrap ci-fast ci-local migrations-local integration-local ci-all doctor secrets.print-age-recipient secrets.encrypt secrets.decrypt backup-now restore-check

up:
	docker compose up -d --build --wait db redis api worker

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

sh:
	docker compose exec api sh -lc "bash || sh"

fmt:
	$(BLACK) . || true

lint: ensure-bootstrap
	@$(RUFF) check .
	@$(BLACK) --check .

type: ensure-bootstrap
	$(MYPY) .

unit: ensure-bootstrap
	mkdir -p $(ART)
	PYTHONUNBUFFERED=1 $(PYTEST) -vv -s -m "not integration and not slow" \
	  -n auto --dist=loadfile --durations=20 \
	| tee $(ART)/unit.log ; test $${PIPESTATUS[0]} -eq 0

unit-all: ensure-bootstrap
	@set -o pipefail; \
	mkdir -p $(ART); \
	PYTHONUNBUFFERED=1 $(PYTEST) -vv -s -m "not integration" -n auto --dist=loadfile --durations=20 2>&1 | tee $(ART)/pytest-unit-all.log; \
	test $${PIPESTATUS[0]} -eq 0

integ:
	$(PYTEST) -q -m integration || true

bootstrap-dev:
	PIP_BREAK_SYSTEM_PACKAGES=1 $(PIP) install -U pip wheel
	PIP_BREAK_SYSTEM_PACKAGES=1 $(PIP) install -U pre-commit mypy pytest-cov
	PIP_BREAK_SYSTEM_PACKAGES=1 $(PIP) install -r requirements-dev.txt
	PIP_BREAK_SYSTEM_PACKAGES=1 $(PIP) install -e packages/awa_common
	pre-commit clean
	pre-commit install
	pre-commit install-hooks
	touch .dev_bootstrapped

ensure-bootstrap:
	@test -f .dev_bootstrapped || $(MAKE) bootstrap-dev

install-dev: bootstrap-dev

qa: ensure-bootstrap
	mkdir -p $(ART)
	pre-commit run --all-files --show-diff-on-failure || true
	@git diff --quiet || (echo "✖ Pre-commit modified files. Commit baseline or run 'make qa-fix'."; exit 1)
	$(MAKE) lint
	$(MAKE) type
	$(MAKE) unit

qa-fix: ensure-bootstrap
	@set -o pipefail; \
	mkdir -p $(ART); \
	if [ -d .git ]; then git config --local --unset-all http.https://github.com/.extraheader || true; fi; \
	pre-commit run --all-files --show-diff-on-failure 2>&1 | tee $(ART)/pre-commit.log || true; \
	git add -A; \
	pre-commit run --all-files --show-diff-on-failure 2>&1 | tee $(ART)/pre-commit.log || true; \
	git add -A; \
	$(RUFF) check . --fix 2>&1 | tee $(ART)/ruff.log; \
	$(BLACK) . 2>&1 | tee $(ART)/black.log; \
	$(MYPY) . 2>&1 | tee $(ART)/mypy.log; \
	PYTHONUNBUFFERED=1 $(PYTEST) -vv -s -m "not integration and not slow" -n auto --dist=loadfile --durations=20 2>&1 | tee $(ART)/pytest-unit.log

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

secrets.print-age-recipient:
	@[ -f "$$SOPS_AGE_KEY_FILE" ] || { echo "Set SOPS_AGE_KEY_FILE to your age private key"; exit 1; }
	@age-keygen -y "$$SOPS_AGE_KEY_FILE" 2>/dev/null | sed 's/^/Recipient: /'

secrets.encrypt:
	@[ "$$SRC" ] || { echo "Usage: make secrets.encrypt SRC=ops/secrets/dev.yaml DST=ops/secrets/dev.enc.yaml"; exit 1; }
	@[ "$$DST" ] || { echo "Usage: make secrets.encrypt SRC=... DST=..."; exit 1; }
	@sops --encrypt "$$SRC" > "$$DST"

secrets.decrypt:
	@[ "$$SRC" ] || { echo "Usage: make secrets.decrypt SRC=ops/secrets/dev.enc.yaml DST=.env.local"; exit 1; }
	@[ "$$DST" ] || { echo "Usage: make secrets.decrypt SRC=... DST=..."; exit 1; }
	@sops --decrypt "$$SRC" > "$$DST"

doctor:
	@echo "Using PY=$(PY)"
	$(PY) -c "import sys,platform; print('exe:', sys.executable); print('ver:', sys.version); print('platform:', platform.platform())"

backup-now:
	@bash ops/backup/bin/backup-now.sh

restore-check:
	@bash ops/backup/bin/restore-check.sh
