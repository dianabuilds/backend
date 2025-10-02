# Product Domain Template (_template)

This is a ready-to-copy template for a product/business domain that follows our project’s architecture and agents.md.

Do not import or run code from `_template` directly. Duplicate it for a new domain or as a starting point for a concrete `product` subdomain implementation.

## How to Use

1) Copy this folder next to it (not inside), rename to your domain name (e.g. `catalog`, `pricing`, or keep `product`).
2) Replace placeholders: names like `Product`, `ProductId`, `ProductEvent` to your actual domain terms if needed.
3) Implement adapters in `adapters/` to match your infra (PostgreSQL/Redis/IAM/etc.).
4) Wire dependencies in `wires.py` and expose a single composition entry (`build_container`).
5) Add API handlers outside the domain layer (in `api/`), mapping HTTP <-> application service DTOs.

## What’s Included

- application: ports (Protocols) and a service with basic use-cases
- domain: entities, value objects, events, errors (pure, no I/O)
- adapters: stubs for repo (SQLAlchemy), outbox (Redis), iam client (external service)
- wires: DI composition to build the service
- tests: skipped unit skeletons to guide coverage

## Agent Instructions (must-do)

- Follow agents.md: Plan → Tests → Code → Self-review → PR.
- Keep boundaries: `api → service → domain → repo → infra`. No business logic in adapters or API.
- Run pre-commit on changed files: `pre-commit run --files <files>`.
- Backend checks: black, ruff (isort), mypy --strict, bandit, vulture, pip-audit.
- Tests: pytest (and hypothesis for property-based if applicable). Keep coverage ≥ 80%.
- Observability: structured logs (trace_id, user_id?), metrics, tracing in adapters; domain stays pure.
- Security: no secrets in code; use settings; validate inputs at boundaries.
- Performance budgets: keep service operations lean; offload I/O to adapters.

## Checklist for a New Domain

- Define domain entities and invariants in `domain/` with dataclasses
- Define ports (Repo, Outbox, IamClient/other) in `application/ports.py`
- Implement `Service` use-cases in `application/services.py` using only the ports
- Provide concrete adapters; include timeouts, retries, and proper error mapping
- Add tests: unit for domain and service, contract tests for adapters via ports
- Wire container in `wires.py` and integrate with app
- Update docs/ADR and API/UI schemas with versioning


### Адаптеры

- `adapters/repo_sql.py` уже содержит минимально рабочую реализацию. Если передать DSN,
  он создаст таблицу `product_template_items`; иначе будет хранить данные в памяти.
  Допишите схему/ORM, как только определите персистентный стор.
- `adapters/iam_client.py` возвращает детерминированные заглушки. Замените вызовом
  вашего IAM (HTTP/gRPC), настройте кэш/ретраи и специфику домена.

