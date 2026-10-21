.PHONY: dev stop logs test test-api test-web migrate seed lint

dev:
	docker compose up --build -d
	@echo "Kingdom Agency is running:"
	@echo "  API:  http://localhost:8000"
	@echo "  Web:  http://localhost:5173"
	@echo "  Docs: http://localhost:8000/docs"

stop:
	docker compose down

logs:
	docker compose logs -f

test: test-api

test-api:
	docker compose exec api pytest -v

test-web:
	docker compose exec web npm test

migrate:
	docker compose exec api alembic upgrade head

migration:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

seed:
	docker compose exec api python -m scripts.seed

lint:
	docker compose exec api ruff check . && docker compose exec api mypy app
