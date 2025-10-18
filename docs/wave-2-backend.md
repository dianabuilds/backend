# Wave 2 — Бэкенд

## Снимок importlinter — 11.10.2025
- Команда: `python -m importlinter.cli lint --config apps/backend/importlinter.ini`.
- Конфигурация: добавлены контракты `layers_product_worlds`, `layers_product_ai`, `layers_product_premium` для новых доменов `apps.backend.domains.product`.
- Результат: нарушений не обнаружено (exit code 0).
- Отчёт: `var/backend-import-lint.txt`.

## Наблюдения и следующие шаги
- `product/ai` и `product/premium` используют упрощённую слойность (`api -> application`/`adapters`), поэтому отдельные контракты зафиксированы до расширения доменных слоёв.
- Для `product/content`, `product/navigation`, `product/quests` и других доменов с инфраструктурой требуется выровнять структуру каталогов, после чего можно объединить контракты через `containers`.
- Дальнейшие проверки: добавить forbidden-правила между доменами после ревизии сервисных фасадов и событийной шины.

## Задача W2-1 — Выстроить доменные границы между product и platform
- **Описание**: устранить прямые импорты платформенных сервисов из продуктовых доменов, выделить фасады/порты и зафиксировать правила в `importlinter`.
- **Шаги выполнения**:
  1. Прогнать `python -m importlinter.cli lint --config apps/backend/importlinter.ini` с новыми контрактами и собрать список пересечений (`var/backend-import-lint.txt`).
  2. Для доменов `apps/backend/domains/product/{nodes,navigation,profile,tags,referrals,...}` заменить прямые импорты `domains.platform.*` на фасады/порты внутри `platform` (например, `domains/platform/iam/application/facade.py`, `domains/platform/events/application/publisher.py`) и зарегистрировать их в контейнерах.
  3. Выровнять структуру `wires.py` и DI в `product/*` и `platform/*`, перевести использование общих фасадов через `apps/backend/app/api_gateway/container_registry.py`.
  4. Обновить `apps/backend/importlinter.ini`, добавив forbidden-контракты `product -> platform` с whitelists для фасадов, и зафиксировать успешный прогон.
  5. Отразить новые границы в `apps/backend/ARCHITECTURE.md` и обновить раздел Wave 2 в `docs/code-audit-plan-2025.md`.
- **Определение готовности (DoR)**: подтверждён список доменов и владельцев, есть текущее дерево импортов и план фасадов.
- **Определение завершения (DoD)**: importlinter проходит без нарушений, контейнеры используют фасады, документация обновлена, публичные API не меняются.
- **Критерии приемки (AC)**:
  - `python -m importlinter.cli lint --config apps/backend/importlinter.ini` возвращает exit code 0 и контракт `product -> platform` без исключений.
  - В `apps/backend/domains/product/*` отсутствуют импорты `domains.platform.*`, кроме фасадов/ports.
  - В `apps/backend/ARCHITECTURE.md` перечислены допустимые зависимости product ↔ platform.
- **Артефакты**: `apps/backend/importlinter.ini`, фасады в `apps/backend/domains/platform/*`, `apps/backend/ARCHITECTURE.md`, обновлённый `var/backend-import-lint.txt`.

## Задача W2-2 — Закрыть ошибки mypy strict (79 шт.)
- **Описание**: устранить ошибки mypy в доменах moderation/nodes/migrations и включить строгие флаги без лишних `ignore`.
- **Шаги выполнения**:
  1. Зафиксировать текущее состояние `mypy.log`, классифицировать ошибки по модулям (`platform/moderation`, `product/nodes`, `migrations`).
  2. Переписать `apps/backend/domains/platform/moderation/application/presenters/enricher.py`, внедрив TypedDict/Protocol вместо нестрогих dict.
  3. Исправить `None`-safe обращения в `apps/backend/domains/product/nodes/api/_memory_utils.py` и связанных сервисах (`application/service.py`).
  4. Аннотировать `apps/backend/migrations/versions/0100_squashed_base.py` (helpers, типы контекста), убрать устаревшие `type: ignore`.
  5. Включить строгие флаги (`warn_unused_ignores`, `disallow-any-generics`) в `pyproject.toml`, прогнать `poetry run mypy --config-file pyproject.toml apps/backend`.
  6. Обновить `docs/backend-testing-strategy.md` раздел типизации с датой и ответственными.
- **Определение готовности (DoR)**: есть актуальный `mypy.log`, согласован список модулей и владельцев, локально настроен mypy.
- **Определение завершения (DoD)**: mypy проходит без ошибок, `type: ignore` используются только с обоснованием, документация обновлена.
- **Критерии приемки (AC)**:
  - `mypy.log` пустой, `poetry run mypy ...` завершился exit code 0.
  - В diff уменьшается количество `type: ignore`, строгие флаги включены.
  - В `docs/backend-testing-strategy.md` зафиксирован статус типизации и дата.
- **Артефакты**: обновлённые файлы доменов, `pyproject.toml`, `mypy.log`, запись в `docs/backend-testing-strategy.md`.

## Задача W2-3 — Разгрузить горячие use-case nodes/moderation/notifications
- **Описание**: устранить дублирование и смешение слоёв в use-case `nodes`, `moderation`, `notifications`, улучшить наблюдаемость и производительность.
- **Шаги выполнения**:
  1. Запустить `scripts/api_benchmark.py --scenarios nodes,moderation,notifications` и обновить `var/api-benchmarks.json`.
  2. Проанализировать `apps/backend/domains/product/nodes/application/service.py`, `apps/backend/domains/platform/moderation/application/service.py`, `apps/backend/domains/platform/notifications/application/service.py` на предмет SRP-нарушений и прямых обращений к инфраструктуре.
  3. Вынести повторяющиеся части в фасады/интеракторы (`application/interactors`), заменить передачу dict на DTO.
  4. Добавить интеграционные тесты (`tests/integration/nodes/test_nodes_hot_paths.py` и аналоги для moderation/notifications) с фиксацией happy/edge-case.
  5. Обновить API-слой (`apps/backend/domains/product/nodes/api/public/*.py`) и OpenAPI (`apps/backend/var/openapi.json`), согласовать изменения с фронтом.
  6. Обновить `docs/code-audit-plan-2025.md` (раздел Wave 2) ссылками на отчёты и результаты.
- **Определение готовности (DoR)**: согласован список сценариев, есть тестовые данные и допуск на интеграционные тесты.
- **Определение завершения (DoD)**: бенчмарки не деградировали (TTFB улучшен ≥5%), тесты зелёные, документация и OpenAPI обновлены, фронт подтверждён.
- **Критерии приемки (AC)**:
  - `var/api-benchmarks.json` показывает улучшение P95 для `/v1/nodes` и `/v1/moderation/cases`.
  - Use-case файлы не содержат прямых SQL/HTTP вызовов, всё вынесено в adapters.
  - Новые интеграционные тесты проходят в CI и приложены к PR.
- **Артефакты**: `var/api-benchmarks.json`, тесты `tests/integration/*`, обновлённые API-модули, `apps/backend/var/openapi.json`.

## Задача W2-4 — Профилировать async pipeline и оптимизировать хранение
- **Описание**: выявить узкие места в асинхронных обработчиках (nodes ingestion, notifications outbox) и оптимизировать индексы/кеши.
- **Шаги выполнения**:
  1. Запустить `pytest -k "async" --durations=20` и собрать профили `apps/backend/domains/platform/notifications` и `apps/backend/domains/product/nodes` с помощью `scripts/async_profiler.py` (или аналога), сохранить результаты в `var/profiling`.
  2. Сгенерировать flamegraph для воркеров (`apps/backend/domains/platform/notifications/worker.py`, `apps/backend/domains/product/nodes/application/embedding_worker.py`).
  3. Выполнить `EXPLAIN ANALYZE` для таблиц `nodes`, `moderation_cases`, `notifications_outbox`, добавить недостающие индексы через миграции (`apps/backend/migrations/versions/*`).
  4. Настроить кеш/TTL в `apps/backend/domains/product/nodes/infrastructure/cache.py`, документировать объём и политику очистки.
  5. Повторно прогнать `scripts/api_benchmark.py` и `pytest`, убедиться в улучшении latency ≥20% и отсутствии регрессий.
  6. Зафиксировать результаты в `docs/code-audit-plan-2025.md` и, при необходимости, создать/обновить `docs/performance-playbook.md`.
- **Определение готовности (DoR)**: доступен стенд/fixture БД, согласованы целевые метрики, профилировщик готов.
- **Определение завершения (DoD)**: flamegraphы приложены, индексы/кеши внедрены, latency улучшена, документация обновлена.
- **Критерии приемки (AC)**:
  - В `var/profiling/nodes-*.svg` и `var/profiling/notifications-*.svg` нет долгих блокировок.
  - Миграции содержат новые индексы, тесты `pytest` зелёные.
  - В `docs/performance-playbook.md` описаны лимиты redis/postgres и триггеры для повторных профилей.
- **Артефакты**: профили `var/profiling/*`, миграции, обновлённые кеш-клиенты, документация.

## Задача W2-5 — Усилить безопасность API (CSRF, rate-limit, секреты)
- **Описание**: проверить IAM и защиту API, закрыть пробелы по CSRF/429 и стандартизировать работу с секретами.
- **Шаги выполнения**:
  1. Проанализировать `apps/backend/domains/platform/iam/security.py` и `apps/backend/app/api_gateway/main.py`, выявить эндпоинты без CSRF/rate-limit.
  2. Добавить middleware/Depends для CSRF во всех POST/PUT/PATCH роутерах `apps/backend/domains/product/*/api`, обновить генерацию токенов.
  3. Настроить rate-limit для публичных маршрутов (`nodes`, `navigation`, `content`) через `apps/backend/app/api_gateway/settings/profile.py`, вынести конфиги в `infra/`.
  4. Перенести секреты в `apps/backend/packages/core/config.py` на `pydantic-settings` со строгой валидацией.
  5. Дополнить тесты `apps/backend/app/tests/test_security_csrf.py` и `apps/backend/app/tests/test_security_rate_limit.py` (создать) — они должны падать при отключении защиты.
  6. Обновить `docs/security-requirements.md` и раздел Wave 2 в `docs/code-audit-plan-2025.md`, синхронизировать с фронтом (CSRF/429 схемы) и OpenAPI (`apps/backend/var/openapi.json`).
- **Определение готовности (DoR)**: есть матрица публичных эндпоинтов, согласованы изменения с DevSecOps и фронтом, готовы сценарии тестов.
- **Определение завершения (DoD)**: все write-эндпоинты защищены CSRF+rate-limit, тесты зелёные, документация и OpenAPI обновлены, фронт подтвердил совместимость.
- **Критерии приемки (AC)**:
  - `pytest -k "security"` проходит, а при отключении middleware тесты падают.
  - OpenAPI описывает `429` и cookie/header `X-CSRF-Token`.
  - `.env` не содержит секретов вне `pydantic-settings`, для каждого параметра есть валидация.
- **Артефакты**: middleware в `apps/backend/app/api_gateway`, тесты `apps/backend/app/tests/test_security_*.py`, `apps/backend/var/openapi.json`, `docs/security-requirements.md`.

### Итоги обновления (10.10.2025)
- Подключён `csrf_protect` ко всем write-эндпоинтам product-доменов, `issue_csrf_token` выдаёт cookie+header и опциональный TTL (`auth_csrf_ttl_seconds`).
- Создан конфиг `apps/backend/infra/security/rate_limits.py`; публичные маршруты nodes/navigation/content используют общие зависимости, конфиг отдаётся через `/v1/settings/profile`.
- `packages.core.config.Settings` переведён на `SecretStr` для чувствительных полей (`auth_jwt_secret`, `admin_api_key`, `smtp_password`, и др.), обновлены вызовы и тесты.
- Добавлены тесты `test_security_csrf.py`, `test_security_rate_limit.py`, OpenAPI экспорт обновлён (`apps/backend/var/openapi.json`).

## Задача W2-6 — Обновить фронтовый API слой под новые контракты
- **Описание**: синхронизировать фронтовые клиенты и типы с изменёнными backend контрактами (nodes, moderation, notifications).
- **Шаги выполнения**:
  1. Экспортировать актуальную схему `python apps/backend/infra/ci/export_openapi.py --output apps/backend/var/openapi.json`.
  2. Обновить/сгенерировать DTO и клиенты в `apps/web/src/shared/api/{nodes,moderation,notifications}` (через `openapi-typescript` или ручное обновление), скорректировать `apps/web/src/shared/api/index.ts`.
  3. Обновить SSR-слой (`apps/web/server/createServer.ts`) и перехватчики в `apps/web/src/shared/api/auth.ts`, обеспечить корректную обработку CSRF/429.
  4. Запустить `npm run test` и привести к зелёному состоянию `apps/web/src/shared/api/*/*.test.ts`, обновить фикстуры.
  5. Зафиксировать изменения в `apps/web/frontend-audit.md` и `docs/code-audit-plan-2025.md` (Wave 2 фронт).
- **Определение готовности (DoR)**: backend схема готова, согласован список затронутых эндпоинтов, определены владельцы модулей.
- **Определение завершения (DoD)**: клиенты и типы обновлены, тесты Vitest зелёные, SSR/клиент работают с новыми контрактами, документация обновлена.
- **Критерии приемки (AC)**:
  - `npm run test` проходит без скипов в `apps/web/src/shared/api/*/*.test.ts`.
  - `apps/web/src/shared/api/index.ts` экспортирует только актуальные клиенты, unused API удалены.
  - В `apps/web/frontend-audit.md` указан апдейт и ссылка на PR.
- **Артефакты**: `apps/backend/var/openapi.json`, файлы `apps/web/src/shared/api`, `apps/web/frontend-audit.md`.

## Задача W2-7 — Поддержать механизмы безопасности на фронте (CSRF/429)
- **Описание**: адаптировать фронтовый клиент к обновлённым правилам безопасности, обеспечить корректный UX при ошибках.
- **Шаги выполнения**:
  1. Обновить `apps/web/src/shared/api/client/csrf.ts` и `apps/web/src/shared/api/client/base.ts`, поддержав новые cookie/header имена и ограничение TTL.
  2. Добавить централизованную обработку 429/403 в `apps/web/src/shared/api/client/base.ts` и проброс через `apps/web/src/shared/ui/ToastProvider.tsx`/`useToast.ts`.
  3. Проверить SSR и при необходимости дополнить `apps/web/server/createServer.ts`, чтобы ответы проксировали CSRF токены.
  4. Создать unit-тесты `apps/web/src/shared/api/client/__tests__/csrf.test.ts` и `apps/web/src/shared/api/client/__tests__/rate-limit.test.ts`, добавить e2e сценарий `apps/web/cypress/e2e/security_rate_limit.cy.ts`.
  5. Обновить раздел «Безопасность» в `apps/web/frontend-audit.md` и синхронизировать статус в `docs/code-audit-plan-2025.md`.
- **Определение готовности (DoR)**: backend предоставил новые правила, UX согласован, подготовлено окружение для e2e.
- **Определение завершения (DoD)**: CSRF токены синхронизируются, 429 обрабатывается с уведомлением, тесты Vitest/Cypress зелёные, документация обновлена.
- **Критерии приемки (AC)**:
  - Vitest тесты для CSRF/429 проходят и падают при отключении защиты.
  - E2E сценарий показывает пользователю уведомление и повторно выполняет действие после таймаута.
  - В `frontend-audit.md` зафиксированы новые правила и дата.
- **Артефакты**: обновлённые файлы `apps/web/src/shared/api/client/*.ts`, тесты (`apps/web/src/shared/api/client/__tests__`, `apps/web/cypress/e2e/security_rate_limit.cy.ts`), `apps/web/frontend-audit.md`.
