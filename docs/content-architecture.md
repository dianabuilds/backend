# Content Architecture

The backend follows a modular design built on FastAPI. Domain modules are located under `apps/backend/app/domains` and contain three layers:

- **API layer** – FastAPI routers handling HTTP requests.
- **Application layer** – services encapsulating business logic.
- **Infrastructure layer** – database models, repositories and external integrations.

Cross‑cutting concerns live in `app/core` (configuration, middleware, metrics). Persistence relies on SQLAlchemy with Alembic migrations in `apps/backend/alembic`.

Metrics and tracing are exposed via Prometheus and OpenTelemetry through the `/metrics` endpoint.
