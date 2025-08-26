.PHONY: test-cov compose-dev db-upgrade db-downgrade db-reset docs

test-cov:
	pytest -q --cov --cov-report=term-missing

docs:
	pydoc-markdown

compose-dev:
	docker compose up -d --wait

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade base

db-reset: db-downgrade db-upgrade
