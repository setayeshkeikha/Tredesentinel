.PHONY: up down logs migrate revision test fmt shell-api shell-worker

up:
	docker-compose up --build

down:
	docker-compose down

logs:
	docker-compose logs -f api worker

migrate:
	docker-compose run --rm migrate

# Usage: make revision msg="add something new"
revision:
	docker-compose run --rm api alembic revision -m "$(msg)"

test:
	docker-compose run --rm api pytest -v -m "not integration"

test-integration:
	docker-compose run --rm api pytest -v -m integration

test-all:
	docker-compose run --rm api pytest -v

shell-api:
	docker-compose exec api bash

shell-worker:
	docker-compose exec worker bash
