.PHONY: install run lint format test test-cov migrate migrate-new docker-build docker-up docker-down docs clean

install:  ## Instalira projekt + dev dependency-je u trenutni (virtualenv) Python
	pip install -e ".[dev]"

run:  ## Pokreće aplikaciju lokalno (SQLite, hot-reload)
	PYTHONPATH=src uvicorn tickethub.main:app --reload

lint:  ## Pokreće ruff linter
	ruff check src tests

format:  ## Auto-formatira/sortira import-e preko ruffa
	ruff check src tests --fix

test:  ## Pokreće pytest
	PYTHONPATH=src pytest -v

test-cov:  ## Pokreće pytest s coverage izvještajem
	PYTHONPATH=src pytest --cov=tickethub --cov-report=term-missing

migrate:  ## Primjenjuje sve Alembic migracije (upgrade head)
	PYTHONPATH=src alembic upgrade head

migrate-new:  ## Generira novu Alembic migraciju: make migrate-new msg="opis promjene"
	PYTHONPATH=src alembic revision --autogenerate -m "$(msg)"

docker-build:  ## Builda Docker image
	docker build -t tickethub:latest .

docker-up:  ## Pokreće cijeli stack (API + Postgres + Redis) preko docker-compose
	docker compose up --build

docker-down:  ## Gasi docker-compose stack
	docker compose down

docs:  ## Generira statičku ReDoc HTML dokumentaciju iz OpenAPI sheme (vidi docs/README.md)
	python scripts/generate_openapi.py
	npx --yes @redocly/cli build-docs openapi.json -o docs/index.html

clean:  ## Briše cache i lokalnu SQLite bazu
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage tickethub.db
	find . -type d -name __pycache__ -exec rm -rf {} +
