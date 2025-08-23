.PHONY: run-backend migrate

run-backend:
	uvicorn apps.backend.app.main:app --reload

migrate:
	alembic -c apps/backend/alembic.ini upgrade head
