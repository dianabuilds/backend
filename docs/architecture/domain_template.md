# Шаблон Домена

Эталонная структура для доменов в `app/domains/<name>`:

- api/: FastAPI-маршруты и контракты (`contracts.md`)
- application/:
  - ports/: контракты зависимостей
  - services/: use-case сервисы
  - policies.py: доменные правила
  - workflows/: DAG сценарии YAML
- infrastructure/:
  - models/: ORM-модели SQLAlchemy
  - repositories/: реализации портов хранения
  - adapters/: внешние интеграции
  - queries/: DAO/ручные запросы
- schema/:
  - openapi.yaml: срез API домена
  - json/: JSON Schema (API/события)
  - sql/: дизайн-спеки миграций (реальная миграция — общий Alembic)
- events/:
  - specs/: схемы событий
  - publisher.py: публикация через общий outbox
- agent/: инструменты/промпты/эвалы для агента
- tests/: unit/contract/e2e
- infra/: policy.yaml, feature_flags.yaml, deployment.yaml
- README.md: паспорт домена, язык и границы
- ADR/: ключевые решения

Скаффолдинг: `python backend/scripts/scaffold_domain.py <name>`.

