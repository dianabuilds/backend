.PHONY: up-local up-dev test seed

DOCKER_COMPOSE = docker compose
UP = $(DOCKER_COMPOSE) up -d --build

up-local:
	APP_ENV_MODE=local $(UP) --profile local

up-dev:
	APP_ENV_MODE=dev $(UP) --profile dev

test:
	APP_ENV_MODE=test $(UP) --profile test
	pytest

seed:
	python scripts/seed_db.py
