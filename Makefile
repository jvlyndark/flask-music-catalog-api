.PHONY: up down seed test lint format

up:
	docker-compose up --build

down:
	docker-compose down

seed:
	python seed.py

test:
	docker-compose exec -e PYTHONPATH=/app -e MONGO_URI_TEST=mongodb://mongo:27017/musiccatalog_test app pytest tests/ -v

lint:
	ruff check . && ruff format --check .

format:
	ruff format .
