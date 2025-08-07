.PHONY: test-cov compose-dev db-upgrade db-downgrade db-reset

test-cov:
	pytest -q --cov --cov-report=term-missing

compose-dev:
	docker compose up -d --wait

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade base

db-reset: db-downgrade db-upgrade
