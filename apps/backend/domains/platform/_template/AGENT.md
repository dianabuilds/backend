# Agent Brief — <your_domain> (platform)

- Тип: platform/system. Узкое API, стабильные контракты, строгие SLO.
- Допустимые изменения: `api/`, `logic/`, `adapters/`, `models/`, `schema/`, `docs/`, `tests/`.
- Запрещено: бизнес-термины продуктовых доменов; кросс-импорты в продуктовые домены.
- Обязательные артефакты: обновлять `docs/DOMAIN.md`, `TESTPLAN.md`, `METRICS.md` при изменениях логики.

Цикл: PLAN → TESTS → CODE → SELF-REVIEW. Контракты (OpenAPI/Events) — additive-only для MINOR/PATCH.

Команды:
- `make schemas-validate` / `make schemas-compat`
- `make migrate-all`
- `make test`

SLO/SLA и бюджеты фиксируются в `docs/METRICS.md` и валидируются бенчами/алертами.
