.PHONY: test-cov compose-dev db-upgrade db-downgrade db-reset docs fmt

test-cov:
	pytest -q --cov --cov-report=term-missing

docs:
	pydoc-markdown

fmt:
	python -m black services/etl/healthcheck.py services/ingest/healthcheck.py

compose-dev:
	docker compose up -d --wait

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade base

db-reset: db-downgrade db-upgrade
