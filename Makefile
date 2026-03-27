.PHONY: up down seed test lint

up:
	docker-compose up --build

down:
	docker-compose down

seed:
	python seed.py

test:
	docker-compose exec -e PYTHONPATH=/app -e MONGO_URI_TEST=mongodb://mongo:27017/musiccatalog_test app pytest tests/ -v

# Placeholder until a linter (ruff or flake8) is added to requirements.txt.
lint:
	@echo "Linter not configured yet."
