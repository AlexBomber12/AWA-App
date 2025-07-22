.PHONY: test-cov compose-dev

test-cov:
pytest -q --cov --cov-report=term-missing

compose-dev:
docker compose up -d --wait
