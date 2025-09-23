# Инструкция для агента — платформенные домены

Всегда начинай разработку платформенного домена с копирования шаблона:
- `apps/backend/domains/platform/_template` → `apps/backend/domains/platform/<your_domain>`

Правила (обязательно):
- Соблюдай структуру шаблона: `api/`, `logic/`, `models/`, `adapters/`, `schema/`, `infra/`, `docs/`, `tests/`.
- API узкое и стабильное, без продуктовых терминов.
- Политики по умолчанию: идемпотентность, rate‑limit, DLQ (если применимо к домену).
- Публичные контракты (OpenAPI/Events) добавляй в `apps/backend/packages/schemas/**` с версионированием.
- Обновляй `docs/DOMAIN.md`, `TESTPLAN.md`, `METRICS.md` при каждом изменении логики.
- Перед PR: `make schemas-validate`, `make schemas-compat`, `make test`.

Допускается удалять лишнее из шаблона, но нарушать слои/структуру — нельзя без блока `<WAIVER>` в PR.

