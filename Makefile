.PHONY: up down seed test lint

up:
	docker-compose up --build

down:
	docker-compose down

seed:
	python seed.py

test:
	pytest tests/ -v

# Placeholder until a linter (ruff or flake8) is added to requirements.txt.
lint:
	@echo "Linter not configured yet."
