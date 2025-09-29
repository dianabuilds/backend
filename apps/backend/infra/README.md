# infra/

Infrastructure assets for the backend:

- ci/ - CI helpers (schema checks, domain scaffolding, import rules).
- dev/ - developer utilities and local environment helpers.
- config/ - shared service configuration (logging, etc.).
- observability/ - OpenTelemetry bootstrap and Prometheus assets.
- constraints/ - pip-compile constraint locks.

Worker entrypoints live in apps/backend/workers/.
