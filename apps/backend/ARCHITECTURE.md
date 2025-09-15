# Архитектура backendDDD (демо)

Цель: монорепо‑каркас для безопасной разработки с ИИ‑агентом. Явные границы, контракт‑центричность, платформенные
сервисы, типизированные настройки и «рельсы» CI.

## Обзор

- Приложение: FastAPI gateway, монтирует роутеры доменов.
- Домены: единый шаблон слоёв `api → application → domain → adapters`, per‑domain миграции.
- Платформа: инфраструктурные способности (напр., события через Redis Streams) с узким API и политиками.
- Контракты: публичные OpenAPI/JSON Schema событий — один источник в `packages/schemas`.
- Настройки: pydantic‑settings, `.env(.local)` для dev, ENV в CI/Prod.

## Дерево (главное)

```
apps/backendDDD/
  app/api_gateway/           # FastAPI + DI (lifespan)
  domains/                   # все домены
    profile/                 # пример продуктового домена
    platform/
      events/                # платформенный домен «события» (Redis Streams)
      _template/             # шаблон для новых платформенных доменов
  packages/
    core/                    # ядро (config/settings, errors, http, redis_outbox)
    domain-registry/         # манифесты доменов (опц.)
    schemas/                 # публичные контракты API/Events
  infra/                     # docker-compose, CI‑скрипты, otel
  AGENTS.md                  # общие инструкции для агента
  ARCHITECTURE.md            # этот документ
```

## Слои домена

- `api/`: тонкие контроллеры FastAPI, валидация DTO, без бизнес‑логики.
- `application/`: use‑cases, координация, транзакции, фича‑флаги, порты (интерфейсы). Здесь вызываем `domain` и
  `adapters` через порты.
- `domain/`: чистые сущности/правила/политики, без I/O и фреймворков.
- `adapters/`: реализация портов (SQL/Redis/HTTP‑клиенты и т.д.).
- `schema/sql/`: Alembic per‑domain (схема БД = имя домена, `version_table_schema`).
- `docs/`: DOMAIN/GLOSSARY/TESTPLAN/METRICS.

Границы: запрещены импорты «вверх» и кросс‑доменные — междоменно только через публичные клиенты/события.

## Платформенные домены

Пример: `domains/platform/events`

- Транспорт: Redis Streams (`events:<topic>`), consumer groups.
- Политики: идемпотентность (ключ по `topic,key,payload_hash`), rate‑limit per topic, DLQ (`events:dlq:*`).
- API: `/v1/events/health`, `/v1/events/stats/{topic}`.
- Релей: чтение XREADGROUP → обработчик → ACK; при ошибке → DLQ → ACK.

## События

- Публикация: доменные сервисы вызывают порт Outbox → адаптер `adapters/outbox_redis.py` →
  `packages/core/redis_outbox.py` (XADD).
- Контракты: `packages/schemas/events/<domain>/*.json`, `additionalProperties` по политике. Совместимость —
  additive‑only для MINOR/PATCH.
- Релей: `domains/platform/events/logic/relay.py`. Запуск: `make run-relay`.

## Настройки

- `packages/core/config.py` (pydantic‑settings):
    - базовые: `APP_ENV`, `APP_DATABASE_URL`, `APP_REDIS_URL`;
    - события: `APP_EVENT_TOPICS`, `APP_EVENT_GROUP`, `APP_EVENT_RATE_QPS`, `APP_EVENT_IDEMPOTENCY_TTL`.
- Источники по приоритету: ENV > `.env.local` > `.env` > дефолты. Пример — `.env.example`.

## DI и точка входа

- Gateway: `app/api_gateway/main.py` — контейнер в lifespan, `include_router(make_router())` для доменов.
- Сборка зависимостей: `app/api_gateway/wires.py` — `load_settings()`, адаптеры и сервисы доменов.

## Контракты и клиенты

- Контракты хранятся централизованно. В CI: валидация и дифф (OpenAPI / JSON Schema событий). Клиенты генерируются из
  схем (скрипт‑плейсхолдер `infra/ci/clients-gen.sh`).

## Тестирование

- Юнит: `domains/<d>/tests/unit` (pytest, hypothesis опц.).
- Контрактные: `tests/contract` (валидация payload/фикстур против схем, Pact опц.).
- Интеграция: Testcontainers (pg/redis), миграции всех доменов (`infra/ci/migrate_all.sh`).
- Evals: сценарные проверки ключевых флоу (`evals/`).

## CI (набросок стадий)

- lint/types → unit → contracts → integration → security → quality → benchmarks → release.
- Гейты: покрытие, дифф контрактов, импорты, security‑сканы, SBOM.

## Шаблоны

- Продуктовый домен: `templates/domain_product/*` (consumers/routes, outbox/subscriber redis, контрактные тесты).
- Платформа: `domains/platform/_template/*` — начинать платформенные домены копированием шаблона (см.
  `domains/platform/AGENT.md`).

## Правила для агента

- Следуй `AGENTS.md`: PLAN → TESTS → CODE → SELF‑REVIEW; держи логику в правильном слое; контракты через PR.
- Любое отступление от границ — через блок `WAIVER` в PR с владельцем и сроком.

## Дальнейшие шаги

- Подключить реальные проверки совместимости контрактов (oasdiff/jsonschema‑diff) и import‑linter в CI.
- Добавить интеграционные тесты для платформенного релея и доменных обработчиков.
- Ввести кодоген клиентов из OpenAPI/событий.
