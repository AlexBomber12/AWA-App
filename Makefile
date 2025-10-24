SHELL := /usr/bin/env bash
PYTHON ?= $(shell command -v python 2>/dev/null || command -v python3 2>/dev/null)

ifeq ($(PYTHON),)
$(error Python interpreter not found; please install python3)
endif

.PHONY: up down logs sh fmt lint test unit integ qa qa-fix install-dev bootstrap ci-fast ci-local migrations-local integration-local ci-all doctor

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

lint:
	$(PYTHON) -m ruff check . || true

unit:
	pytest -q -m "not integration" || true

integ:
	pytest -q -m integration || true

install-dev:
	@PIP_BREAK_SYSTEM_PACKAGES=1 $(PYTHON) -m pip install -U pre-commit ruff black mypy pytest-cov
	@PIP_BREAK_SYSTEM_PACKAGES=1 $(PYTHON) -m pip install -r requirements-dev.txt
	@PIP_BREAK_SYSTEM_PACKAGES=1 $(PYTHON) -m pip install -e packages/awa_common
	@if [ -d .git ]; then \
		git config --local --unset-all http.https://github.com/.extraheader || true; \
		pre-commit clean; \
		if [ -n "$${PRE_COMMIT_AUTOUPDATE:-}" ]; then pre-commit autoupdate; fi; \
		pre-commit install -f; \
		pre-commit install-hooks; \
	fi

qa: install-dev
	@set -o pipefail; \
	mkdir -p .local-artifacts; \
	if [ -d .git ]; then git config --local --unset-all http.https://github.com/.extraheader || true; fi; \
	pre-commit run --all-files --show-diff-on-failure 2>&1 | tee .local-artifacts/pre-commit.log; \
	status=$${PIPESTATUS[0]}; \
	if ! git diff --quiet; then \
		echo "✖ Pre-commit modified files. Commit baseline or run 'make qa-fix'."; \
		exit 1; \
	fi; \
	test $$status -eq 0 || exit $$status; \
	$(PYTHON) -m ruff check . 2>&1 | tee .local-artifacts/ruff.log; \
	status=$${PIPESTATUS[0]}; test $$status -eq 0 || exit $$status; \
	$(PYTHON) -m black --check . 2>&1 | tee .local-artifacts/black.log; \
	status=$${PIPESTATUS[0]}; test $$status -eq 0 || exit $$status; \
	$(PYTHON) -m mypy . 2>&1 | tee .local-artifacts/mypy.log; \
	status=$${PIPESTATUS[0]}; test $$status -eq 0 || exit $$status; \
	pytest -q -m "not integration" 2>&1 | tee .local-artifacts/pytest-unit.log; \
	status=$${PIPESTATUS[0]}; test $$status -eq 0 || exit $$status

qa-fix: install-dev
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
	pytest -q -m "not integration" 2>&1 | tee .local-artifacts/pytest-unit.log

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
