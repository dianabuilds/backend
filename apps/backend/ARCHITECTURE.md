# Архитектура backend

Проект организован как моно‑репозиторий для сервисов FastAPI и доменных пакетов. Главная цель – изолировать домены, строго описать контракты и упростить сопровождение (CI, миграции, тесты) без неявных зависимостей.

## Обзор

- **API Gateway**: модуль `app/api_gateway` на FastAPI. Он отвечает только за сборку DI-контейнера, регистрацию роутеров доменов и глобальные middleware/метрики.
- **Домены**: в каталоге `apps/backend/domains/<kind>/<name>` с единым шаблоном слоёв `api → application → domain → adapters`.
- **Платформа**: общие сервисы (уведомления, moderation, flags, events, telemetry и т.д.) — живут в `platform.*` и предоставляют узкие порты для продуктовых команд.
- **Контракты**: JSON Schema / OpenAPI в `apps/backend/packages/schemas` и unit/integration тесты в `tests/**` — единственный источник правды для публичных интерфейсов.
- **Настройки**: Pydantic settings (`packages/core/config.py`), многоуровневые `.env` + строгая типизация mypy.

## Дерево (основные каталоги)

```
app/
  api_gateway/               # FastAPI, DI, routers, middleware
apps/backend/
  domains/
    platform/
      notifications/
      moderation/
      ...
    product/
      profile/
      navigation/
      ...
  packages/
    core/                    # общие утилиты (config, db, redis, errors)
    schemas/                 # контракты API/Events
  infra/                     # docker-compose, CI скрипты, observability
  docs/                      # внутренняя документация
  migrations/                # Alembic миграции по доменам
stubs/slugify/               # локальный typeshed для mypy
```

## Слои домена

- `api/` — тонкие контроллеры FastAPI, только валидация запрос/ответ, без бизнес-логики.
- `application/` — команды и запросы (use-case функции), typed presenters и порты. В application-слое больше нет `UseCaseResult`: функции возвращают итоговые DTO/TypedDict.
- `domain/` — чистые сущности, value-objects, политики. Нет I/O и внешних зависимостей.
- `adapters/` — инфраструктура (SQL, Redis, внешние API). Каждый адаптер реализует интерфейсы из `application`.

## Решения последнего рефакторинга

- Все домены переведены на typed presenters + `commands/queries` (вместо временных фасадов и `UseCaseResult`). API-слой теперь работает напрямую с готовыми структурами.
- Библиотека `slugify` закрыта локальным stub`ом (`stubs/slugify/__init__.pyi`), что позволило включить строгий mypy без игноров.
- Раскладка `app/api_gateway` вынесена из `apps/backend/app` в отдельный пакет `app/`, чтобы устранить дублирование путей (`__main__` vs `apps.backend.app`).
- sql/adapters возвращают строго типизированные `dict[str, Any]` (например, `redis_bus.to_payload`, `moderation/adapters/sql/storage`).
- Добавлены тесты уровня `tests/integration` для проверки новых маршрутов и миграций (notifications, moderation, flags и т.д.).

## Mypy и качество

- mypy запускается в строгом режиме (`strict = true`, `explicit_package_bases = true`, `namespace_packages = true`).
- Добавлены точечные stubs вместо глобальных `ignore_missing_imports`.
- Архитектурные правила контролируются `importlinter.ini` и unit/integration тестами.

## Тесты

- `tests/unit/**` — покрытие application/presenter/adapter логики.
- `tests/integration/**` — быстрые smoke-тесты API Gateway, Redis/SQL адаптеров.
- `tests/platform/moderation/**` — доменные сценарии (appeals, tickets, content) без HTTP слоя.

## Хранилище знаний

- `docs/feature_flags_sql_plan.md` — подробный playbook по SQL флагам.
- `docs/worker-platform.md` — запуск воркеров/cron.
- ADR (в `adr/`) фиксируют ключевые архитектурные решения и эволюцию доменов.

