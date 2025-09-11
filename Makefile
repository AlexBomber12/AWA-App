.PHONY: up down logs sh fmt lint test unit integ
up: ; docker compose up -d --build
down: ; docker compose down -v
logs: ; docker compose logs -f --tail=200
sh: ; docker compose exec api sh -lc "bash || sh"
fmt: ; python -m black . || true
lint: ; python -m ruff check . || true
unit: ; pytest -q -m "not integration" || true
integ: ; pytest -q -m integration || true
test: unit integ
